"""
ParallelKDEpy: Python wrapper for ParallelKDE.jl
"""

from importlib.metadata import version as _pkg_version, PackageNotFoundError
from .wrapper import DensityEstimation, Grid, initialize_dirac_sequence

try:
    # Prefer installed dist metadata
    __version__ = _pkg_version("parallelkdepy")
except PackageNotFoundError:
    # Fallback to file updated at build time
    try:
        from ._version import __version__
    except Exception:
        __version__ = "0+unknown"

del _pkg_version, PackageNotFoundError

__all__ = ["__version__", "DensityEstimation", "Grid", "initialize_dirac_sequence"]
