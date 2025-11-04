"""Atlas Orchestrator package exposing version metadata and public interfaces."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("atlas-orchestrator")
except PackageNotFoundError:  # pragma: no cover - fallback for editable installs
    __version__ = "0.2.0"

__all__ = ["__version__"]

