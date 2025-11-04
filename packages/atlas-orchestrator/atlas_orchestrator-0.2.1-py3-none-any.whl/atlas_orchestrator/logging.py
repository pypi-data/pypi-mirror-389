"""Logging bootstrap utilities."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import LoggingConfig

_LOG_FORMATS: dict[str, str] = {
    "structured": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "plain": "%(levelname)s - %(message)s",
}


def configure_logging(config: LoggingConfig, *, force: bool = True) -> None:
    """Configure the root logger according to the supplied configuration."""

    level = _parse_level(config.level)
    handler = _build_handler(config)
    formatter = _build_formatter(config)
    handler.setFormatter(formatter)

    logging.basicConfig(level=level, handlers=[handler], force=force)


def _parse_level(level: str) -> int:
    resolved = logging.getLevelName(level.upper())
    if isinstance(resolved, int):
        return resolved
    return logging.INFO


def _build_handler(config: LoggingConfig) -> logging.Handler:
    destination = config.destination.lower()
    if destination == "stdout":
        return _rich_handler() or logging.StreamHandler(sys.stdout)
    if destination == "stderr":
        return _rich_handler() or logging.StreamHandler(sys.stderr)

    path = Path(config.destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return logging.FileHandler(path)


def _build_formatter(config: LoggingConfig) -> logging.Formatter:
    pattern = _LOG_FORMATS.get(config.format, _LOG_FORMATS["plain"])
    return logging.Formatter(pattern)


def _rich_handler() -> logging.Handler | None:
    try:
        from rich.logging import RichHandler
    except ImportError:
        return None
    return RichHandler(rich_tracebacks=True, markup=True)


__all__ = ["configure_logging"]

