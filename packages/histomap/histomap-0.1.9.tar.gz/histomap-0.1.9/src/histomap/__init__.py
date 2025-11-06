from .histomap import histomap
from .umap import umap

# Expose version and print on import
try:
    from importlib.metadata import version as _get_version, PackageNotFoundError
except Exception:
    _get_version = None
    class PackageNotFoundError(Exception):
        pass

__version__ = "unknown"
if _get_version is not None:
    try:
        __version__ = _get_version("histomap")
    except PackageNotFoundError:
        pass
    except Exception:
        pass

print(f"histomap version {__version__}")