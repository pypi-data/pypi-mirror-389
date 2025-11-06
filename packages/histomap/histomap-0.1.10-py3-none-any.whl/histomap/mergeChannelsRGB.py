#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
mergeChannelsRGB
----------------

Lazy conversion of a multi-channel OME-TIFF (or similar) into an RGB image,
using tifffile + dask + zarr.

This version is designed for H&E or other already-RGB-like images:
- No percentile normalization
- No gamma correction
- Just linear rescaling from the source dtype to [0,1] and then to uint8/16

It also:
- Handles pyramidal/multiscale OME-TIFFs where tifffile.aszarr returns a Zarr group
  (fixes `ContainsGroupError: path '' contains a group` by selecting component "0").
- Can be used from Python or as a CLI script.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence, Tuple, Union

import dask.array as da
import numpy as np
import tifffile
from dask.diagnostics import ProgressBar

try:
    import zarr
    from zarr.errors import ContainsGroupError
except Exception:  # older zarr or not installed (shouldn't happen if using aszarr)
    zarr = None

    class ContainsGroupError(Exception):
        pass


ArrayLike = Union[np.ndarray, "da.Array"]


# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------


def _axes_take(
    arr: da.Array, axes: str, axis_char: str, index: int
) -> tuple[da.Array, str]:
    """
    Take a single index along a given axis (e.g., T or Z) if it exists,
    and remove that axis from the axes string.
    """
    if axis_char not in axes:
        return arr, axes
    ax = axes.index(axis_char)
    index = max(0, min(index, arr.shape[ax] - 1))
    arr = arr.take(index, axis=ax)
    axes = axes[:ax] + axes[ax + 1 :]
    return arr, axes


def _normalize_to_cyx(arr: da.Array, axes: str) -> tuple[da.Array, str]:
    """
    Ensure array is in (C, Y, X) order.
    Supports common axes patterns such as:
      - "CYX"
      - "YXC"
    Assumes T/Z/S have already been squeezed out.
    """
    if axes == "CYX":
        return arr, axes

    if axes == "YXC":
        arr = arr.transpose(2, 0, 1)
        axes = "CYX"
        return arr, axes

    raise ValueError(
        f"Unsupported axes layout '{axes}' after T/Z/S selection; "
        f"expected 'CYX' or 'YXC' but got shape {arr.shape}."
    )


def _open_dask_from_zstore(zstore) -> da.Array:
    """
    Robustly open a dask array from a zarr store returned by tifffile.aszarr.

    - If the root is an array, just use da.from_zarr(zstore).
    - If the root is a group (pyramidal OME-TIFF), pick component "0"
      (the highest resolution level) by default.
    """
    # Simple case: root is an array
    try:
        return da.from_zarr(zstore)
    except ContainsGroupError:
        pass

    # Root is a group; select level "0" if possible
    try:
        return da.from_zarr(zstore, component="0")
    except Exception:
        # Fallback: inspect the group and take first array-like key
        if zarr is None:
            raise
        g = zarr.open_group(store=zstore, path="")
        keys = list(getattr(g, "array_keys", lambda: [])())
        if not keys:
            keys = list(getattr(g, "group_keys", lambda: [])())
        if not keys:
            raise RuntimeError("Could not find any arrays inside zarr group.")
        return da.from_zarr(zstore, component=keys[0])


def _to_uint(arr_cyx: da.Array, bitdepth: int = 8) -> da.Array:
    """
    Convert (C,Y,X) float in [0,1] to uint8 or uint16.
    """
    if bitdepth == 8:
        return (arr_cyx * 255).round().astype("uint8")
    if bitdepth == 16:
        return (arr_cyx * 65535).round().astype("uint16")
    raise ValueError(f"Unsupported bitdepth={bitdepth}; expected 8 or 16.")


# -------------------------------------------------------------------------
# Main function
# -------------------------------------------------------------------------


def mergeChannelsRGB(
    input_path: Union[str, Path],
    order: Sequence[int] = (0, 1, 2),
    z_index: int = 0,
    t_index: int = 0,
    bitdepth: int = 8,
    output_path: Optional[Union[str, Path]] = None,
    zarr_chunks: Optional[Tuple[int, int, int]] = None,
    series_index: int = 0,
    scheduler: Optional[str] = None,
    show_progress: bool = True,
    return_data: bool = True,
) -> Optional[np.ndarray]:
    """
    Merge a 3-channel OME-TIFF into an RGB image with minimal processing.

    - No percentile normalization or gamma correction.
    - Just linear rescaling from the source dtype to [0,1], then to uint8/uint16.
    - Preserves original H&E color balance as much as possible.

    Parameters
    ----------
    input_path : str or Path
        Input OME-TIFF path.
    order : sequence of int, default (0,1,2)
        Channel indices to map onto R,G,B (in the C-axis of the array).
    z_index : int, default 0
        Z slice to select if a Z axis is present.
    t_index : int, default 0
        Timepoint to select if a T axis is present.
    bitdepth : int, default 8
        Output bit depth: 8 or 16.
    output_path : str or Path, optional
        If provided, save the RGB image to this path (TIFF).
    zarr_chunks : tuple(int,int,int), optional
        Desired dask chunking in (C,Y,X). If None, use zarr-default chunks.
    series_index : int, default 0
        TiffFile.series index to use.
    scheduler : str, optional
        Dask scheduler to use for compute (e.g. "threads", "single-threaded").
    show_progress : bool, default True
        If True, show a dask progress bar during computation.
    return_data : bool, default True
        If True, return the RGB image as a NumPy array (Y,X,3). If False,
        compute only for saving and return None.

    Returns
    -------
    rgb : np.ndarray (Y, X, 3) or None
        The RGB image, or None if return_data is False.
    """
    input_path = Path(input_path)

    # --- open TIFF + aszarr lazily ---
    with tifffile.TiffFile(str(input_path)) as tf:
        if series_index < 0 or series_index >= len(tf.series):
            raise IndexError(
                f"series_index {series_index} out of range (0..{len(tf.series)-1})"
            )
        series = tf.series[series_index]
        axes = series.axes  # e.g., "CYX", "YXC", "TCYX", etc.
        zstore = tf.aszarr(series=series)

    # --- dask from zarr (handle group vs array) ---
    arr = _open_dask_from_zstore(zstore)  # shape matches 'axes'

    # --- select T/Z/S if present ---
    arr, axes = _axes_take(arr, axes, "T", t_index)
    arr, axes = _axes_take(arr, axes, "Z", z_index)
    arr, axes = _axes_take(arr, axes, "S", 0)

    # --- normalize axes to (C,Y,X) ---
    arr, axes = _normalize_to_cyx(arr, axes)  # -> (C,Y,X)

    # --- optional rechunk in CYX layout ---
    if zarr_chunks is not None:
        arr = arr.rechunk(zarr_chunks)

    # --- linear scaling from original dtype to [0,1] ---
    orig_dtype = arr.dtype
    arr = arr.astype("float32")

    if np.issubdtype(orig_dtype, np.integer):
        info = np.iinfo(orig_dtype)
        arr = arr / float(info.max)
    else:
        arr = da.clip(arr, 0.0, 1.0)

    # --- select channels and map to RGB ---
    if len(order) != 3:
        raise ValueError(f"'order' must have length 3 (R,G,B). Got {order}")
    c = arr.shape[0]
    if max(order) >= c:
        raise ValueError(f"Channel indices {order} exceed available channels 0..{c-1}.")

    rgb_cyx = da.stack([arr[o] for o in order], axis=0)  # (3,Y,X)

    # --- convert to uint8 / uint16 ---
    rgb_cyx_uint = _to_uint(rgb_cyx, bitdepth=bitdepth)  # (3,Y,X)
    rgb_yxc = rgb_cyx_uint.transpose(1, 2, 0)  # (Y,X,3)

    # --- compute, with optional progress bar ---
    if show_progress:
        with ProgressBar():
            rgb_np = rgb_yxc.compute(scheduler=scheduler)
    else:
        rgb_np = rgb_yxc.compute(scheduler=scheduler)

    # --- save if requested ---
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tifffile.imwrite(str(output_path), rgb_np, photometric="rgb")

    return rgb_np if return_data else None


# -------------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------------


def _parse_args():
    p = argparse.ArgumentParser(
        description="Merge multi-channel OME-TIFF into RGB (lazy, minimal processing)."
    )
    p.add_argument("input", help="Input OME-TIFF path")
    p.add_argument(
        "-o",
        "--output",
        dest="output",
        required=True,
        help="Output RGB TIFF path",
    )
    p.add_argument(
        "--order",
        nargs=3,
        type=int,
        default=(0, 1, 2),
        help="Channel indices for R G B (default: 0 1 2)",
    )
    p.add_argument("--z-index", type=int, default=0, help="Z index if Z axis present")
    p.add_argument("--t-index", type=int, default=0, help="T index if T axis present")
    p.add_argument(
        "--bitdepth",
        type=int,
        default=8,
        choices=[8, 16],
        help="Bit depth (8 or 16, default: 8)",
    )
    p.add_argument(
        "--series-index",
        type=int,
        default=0,
        help="TiffFile.series index (default: 0)",
    )
    p.add_argument(
        "--scheduler",
        type=str,
        default=None,
        help="Dask scheduler (e.g. 'threads', 'processes', 'single-threaded')",
    )
    p.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable dask progress bar",
    )
    return p.parse_args()


def main():
    args = _parse_args()
    mergeChannelsRGB(
        input_path=args.input,
        output_path=args.output,
        order=args.order,
        z_index=args.z_index,
        t_index=args.t_index,
        bitdepth=args.bitdepth,
        series_index=args.series_index,
        scheduler=args.scheduler,
        show_progress=not args.no_progress,
        return_data=False,
    )


if __name__ == "__main__":
    main()
