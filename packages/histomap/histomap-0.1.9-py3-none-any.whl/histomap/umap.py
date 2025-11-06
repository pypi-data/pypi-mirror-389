"""
UMAP embedding utility for SpatialData/WSIData tables, with optional GPU acceleration via RAPIDS cuML.

Usage:
    from histomap.umap import umap
    sda = umap(sda_or_wsi, table="my_table", layer=None, sample_n=5000, sample_frac=None)

This will compute a 2D UMAP embedding of the selected table's data (from AnnData.X or a named layer)
and save it into adata.obsm['X_umap'].

If GPU is available and RAPIDS (cuml + cupy) is installed, the function will use the GPU automatically.
Otherwise, it falls back to `umap-learn` on CPU.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

try:
    # CPU backend
    import umap as umap_learn
except Exception as _e_umap:
    umap_learn = None  # type: ignore

# Optional GPU backend
_cuml = None
_cupy = None
try:
    import cupy as _cp
    _cupy = _cp
    import cuml
    _cuml = cuml
except Exception:
    pass


def _gpu_available() -> bool:
    """Detect if GPU is available and RAPIDS (cuml + cupy) can be used."""
    try:
        if _cupy is None or _cuml is None:
            return False
        # Check device count via CUDA runtime
        try:
            return _cupy.cuda.runtime.getDeviceCount() > 0
        except Exception:
            return False
    except Exception:
        return False


def umap(
    sda_or_wsi,
    table: str,
    *,
    layer: Optional[str] = None,
    sample_n: Optional[int] = None,
    sample_frac: Optional[float] = None,
    embed_full: bool = True,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    n_components: int = 2,
    random_state: int = 0,
    target_key: str = "X_umap",
    prefer_gpu: str = "auto",  # "auto" | "cpu" | "gpu"
):
    """
    Compute a UMAP embedding for the selected table inside a SpatialData/WSIData-like object and
    save the result to `adata.obsm[target_key]`.

    Parameters
    - sda_or_wsi: An object with a `tables` dict mapping table names to AnnData.
    - table: Name of the table to use.
    - layer: AnnData layer name to use. If None, use `adata.X`.
    - sample_n: Optional number of rows to sample when fitting the UMAP model.
    - sample_frac: Optional fraction (0-1] of rows to sample when fitting the model.
    - n_neighbors, min_dist, n_components: UMAP hyperparameters.
    - random_state: RNG seed for reproducibility (sampling and UMAP init).
    - target_key: Key to write embedding into `adata.obsm[target_key]`.
    - prefer_gpu: "auto" (default) will use GPU if available; "gpu" forces GPU (errors if unavailable);
                  "cpu" forces CPU path.

    Returns
    - The updated SpatialData/WSIData-like object with the embedding saved into `adata.obsm[target_key]`.
    """
    # Resolve AnnData from provided object
    if not hasattr(sda_or_wsi, "tables"):
        raise TypeError("Expected an object with a 'tables' attribute containing AnnData tables.")
    if table not in getattr(sda_or_wsi, "tables"):
        raise KeyError(f"Table '{table}' not found in provided object.")
    adata = sda_or_wsi.tables[table]

    # Choose matrix source
    if layer is None:
        X = adata.X
    else:
        if not hasattr(adata, "layers") or layer not in adata.layers:
            raise KeyError(f"Layer '{layer}' not found in adata.layers.")
        X = adata.layers[layer]

    n = X.shape[0]
    if n_components <= 0:
        raise ValueError("n_components must be >= 1")

    # Create sample indices if requested
    rng = np.random.default_rng(random_state)
    sample_inds = None
    if sample_n is not None or sample_frac is not None:
        if sample_n is not None:
            k = int(sample_n)
            k = max(2, min(k, n))
        else:
            frac = float(sample_frac)
            if not (0 < frac <= 1):
                raise ValueError("sample_frac must be in (0, 1]")
            k = max(2, min(n, int(np.round(n * frac))))
        sample_inds = np.sort(rng.choice(n, size=k, replace=False))

    # Select backend
    use_gpu = False
    if prefer_gpu == "gpu":
        use_gpu = True
    elif prefer_gpu == "cpu":
        use_gpu = False
    else:  # auto
        use_gpu = _gpu_available()

    # Build model & fit
    if use_gpu:
        if _cuml is None or _cupy is None:
            raise RuntimeError("GPU backend requested, but RAPIDS (cuml + cupy) is not available.")
        model = _cuml.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=n_components,
            random_state=random_state,
        )
        # Prepare data for GPU (dense float32)
        # Convert scipy.sparse or numpy arrays to cupy dense
        try:
            import scipy.sparse as sp
        except Exception:
            sp = None  # type: ignore
        if sp is not None and sp.issparse(X):
            X_dense = X.toarray().astype(np.float32, copy=False)
        else:
            X_dense = np.asarray(X, dtype=np.float32)
        X_gpu = _cupy.asarray(X_dense)

        if sample_inds is not None:
            Xs_gpu = X_gpu[sample_inds]
            model.fit(Xs_gpu)
            if embed_full:
                try:
                    emb_gpu = model.transform(X_gpu)
                except Exception:
                    # Fallback: fit on full data if transform fails
                    emb_gpu = model.fit_transform(X_gpu)
            else:
                try:
                    emb_s_gpu = model.transform(Xs_gpu)
                except Exception:
                    emb_s_gpu = model.fit_transform(Xs_gpu)
                emb_gpu = _cupy.full((n, n_components), _cupy.nan, dtype=_cupy.float32)
                emb_gpu[sample_inds] = emb_s_gpu
        else:
            emb_gpu = model.fit_transform(X_gpu)
        emb = _cupy.asnumpy(emb_gpu)

    else:
        if umap_learn is None:
            raise ImportError(
                "umap-learn is required for CPU UMAP. Please install it, e.g., 'pip install umap-learn'."
            )
        model = umap_learn.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=n_components,
            random_state=random_state,
            metric="euclidean",
        )
        if sample_inds is not None:
            # Fit on sample, then transform full or embed only sample
            Xs = X[sample_inds]
            model.fit(Xs)
            if embed_full:
                try:
                    emb = model.transform(X)
                except Exception:
                    # Fallback: fit on full data if transform is not available
                    emb = model.fit_transform(X)
            else:
                try:
                    emb_sample = model.transform(Xs)
                except Exception:
                    emb_sample = model.fit_transform(Xs)
                emb = np.full((n, n_components), np.nan, dtype=np.float32)
                emb[sample_inds] = np.asarray(emb_sample, dtype=np.float32)
        else:
            emb = model.fit_transform(X)

    # Save into obsm
    adata.obsm[target_key] = np.asarray(emb)

    return sda_or_wsi


# CLI entry point
import argparse
import spatialdata as sd

def main():
    parser = argparse.ArgumentParser(
        description="Compute UMAP embedding for a SpatialData table and write back to the dataset"
    )
    parser.add_argument("input", help="Path to SpatialData .zarr directory")
    parser.add_argument("--table", required=True, help="Table name in sda.tables to use")
    parser.add_argument("--layer", default=None, help="AnnData layer name to use (default: X)")
    parser.add_argument("--sample-n", type=int, default=None, help="Number of rows to sample for fitting")
    parser.add_argument("--sample-frac", type=float, default=None, help="Fraction of rows to sample for fitting (0-1]")
    parser.add_argument("--embed-full", action="store_true", help="Transform all rows after fitting on sample (default)")
    parser.add_argument("--no-embed-full", dest="embed_full", action="store_false", help="Only embed sampled rows and fill others with NaN")
    parser.set_defaults(embed_full=True)
    parser.add_argument("--n-neighbors", type=int, default=15)
    parser.add_argument("--min-dist", type=float, default=0.1)
    parser.add_argument("--n-components", type=int, default=2)
    parser.add_argument("--random-state", type=int, default=0)
    parser.add_argument("--target-key", default="X_umap")
    parser.add_argument("--prefer-gpu", choices=["auto", "cpu", "gpu"], default="auto")

    args = parser.parse_args()

    sda = sd.read_zarr(args.input)
    sda = umap(
        sda,
        table=args.table,
        layer=args.layer,
        sample_n=args.sample_n,
        sample_frac=args.sample_frac,
        embed_full=args.embed_full,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist,
        n_components=args.n_components,
        random_state=args.random_state,
        target_key=args.target_key,
        prefer_gpu=args.prefer_gpu,
    )

    # Write back to the same path (overwrite)
    wrote = False
    try:
        sda.write_zarr(args.input, overwrite=True)
        wrote = True
    except Exception:
        pass
    if not wrote:
        try:
            sd.write_zarr(sda, args.input, overwrite=True)
            wrote = True
        except Exception:
            pass
    if not wrote:
        try:
            sda.write(args.input)
            wrote = True
        except Exception:
            pass
    if not wrote:
        raise RuntimeError(
            "Failed to write SpatialData back to path. Please ensure your SpatialData version supports writing to Zarr."
        )

    # Determine backend used for message
    if args.prefer_gpu == "gpu":
        backend = "gpu"
    elif args.prefer_gpu == "cpu":
        backend = "cpu"
    else:
        backend = "gpu" if _gpu_available() else "cpu"

    E = sda.tables[args.table].obsm[args.target_key]
    print(
        f"Wrote embedding to {args.input} in table '{args.table}' obsm['{args.target_key}'] "
        f"using backend={backend}. Shape={E.shape}"
    )


if __name__ == "__main__":
    main()