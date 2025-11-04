"""Pytest orchestration helpers for validation."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class PytestReport:
    """Outcome data from a pytest invocation."""

    exit_code: int
    total: int
    passed: int
    failed: int
    errors: int
    duration: float
    output: str

    @property
    def status(self) -> str:
        if self.exit_code == 0:
            return "passed"
        return "failed"


class PytestRunner:
    """Execute pytest and parse summary statistics from its output."""

    def __init__(self, *, project_root: Path | None = None) -> None:
        self._project_root = Path(project_root or Path.cwd())

    def run(self, args: Sequence[str] | None = None) -> PytestReport:
        if os.environ.get("ATLAS_ORCHESTRATOR_VALIDATION_DRY_RUN", "").lower() in {
            "1",
            "true",
            "yes",
        }:
            return PytestReport(
                exit_code=0,
                total=0,
                passed=0,
                failed=0,
                errors=0,
                duration=0.0,
                output="validation dry-run: pytest execution skipped",
            )

        command = [sys.executable, "-m", "pytest", "-q"]
        if args:
            command.extend(args)
        process = subprocess.run(
            command,
            cwd=self._project_root,
            capture_output=True,
            text=True,
        )
        summary = self._parse_summary(process.stdout + process.stderr)
        return PytestReport(
            exit_code=process.returncode,
            total=int(summary.get("total", 0)),
            passed=int(summary.get("passed", 0)),
            failed=int(summary.get("failed", 0)),
            errors=int(summary.get("errors", 0)),
            duration=float(summary.get("duration", 0.0)),
            output=(process.stdout + process.stderr).strip(),
        )

    @staticmethod
    def _parse_summary(output: str) -> dict[str, float | int]:
        summary: dict[str, float | int] = {}
        for line in output.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if "passed" in stripped and "seconds" in stripped:
                tokens = stripped.replace("=", " ").replace(",", " ").split()
                duration_seen = False
                for token in tokens:
                    if token.endswith("passed"):
                        summary["passed"] = int(token.replace("passed", ""))
                    elif token.endswith("failed"):
                        summary["failed"] = int(token.replace("failed", ""))
                    elif token.endswith("errors"):
                        summary["errors"] = int(token.replace("errors", ""))
                    elif not duration_seen and token.replace(".", "", 1).isdigit():
                        summary["duration"] = float(token)
                        duration_seen = True
                passed = int(summary.get("passed", 0))
                failed = int(summary.get("failed", 0))
                errors = int(summary.get("errors", 0))
                summary.setdefault("total", passed + failed + errors)
        return summary


__all__ = ["PytestReport", "PytestRunner"]
