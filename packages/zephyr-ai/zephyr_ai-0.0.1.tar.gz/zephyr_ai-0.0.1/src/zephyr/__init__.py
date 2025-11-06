"""Zephyr orchestration SDK public interface."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("zephyr-ai")
except PackageNotFoundError:  # pragma: no cover - placeholder until package installed
    __version__ = "0.0.0"

__all__ = ["__version__"]
