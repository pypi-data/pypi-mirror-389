from __future__ import annotations

import logging
from pathlib import Path

from atlas_orchestrator.config import LoggingConfig
from atlas_orchestrator.logging import configure_logging


def test_configure_logging_stdout() -> None:
    configure_logging(LoggingConfig(destination="stdout", format="plain", level="INFO"))
    logger = logging.getLogger("atlas_orchestrator.test")
    logger.info("example")


def test_configure_logging_file(tmp_path: Path) -> None:
    log_file = tmp_path / "atlas_orchestrator.log"
    configure_logging(LoggingConfig(destination=str(log_file), format="structured", level="DEBUG"))
    logging.getLogger("atlas_orchestrator.test").debug("file output")
    assert log_file.exists()

