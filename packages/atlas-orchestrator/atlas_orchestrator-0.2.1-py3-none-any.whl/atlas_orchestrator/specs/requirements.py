"""Parsing and querying specification requirements documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Requirement:
    """Structured requirement extracted from product documentation."""

    id: str
    section: str
    text: str


class RequirementsCatalog:
    """Lightweight lookup for requirements relevant to spec modules."""

    def __init__(self, requirements: Sequence[Requirement]) -> None:
        self._requirements = list(requirements)

    def find_related(
        self,
        keywords: Iterable[str],
        *,
        limit: int | None = 5,
    ) -> list[Requirement]:
        tokens = {
            token
            for keyword in keywords
            for token in _tokenise(keyword)
            if token
        }
        if not tokens:
            return []

        scored: list[tuple[int, Requirement]] = []
        for requirement in self._requirements:
            haystack = _tokenise(requirement.text) | _tokenise(requirement.section)
            score = len(tokens & haystack)
            if score:
                scored.append((score, requirement))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = [requirement for _, requirement in scored]
        if limit is None:
            return results
        return results[:limit]

    @classmethod
    def from_markdown(cls, path: Path) -> "RequirementsCatalog":
        if not path.exists():
            return cls([])
        requirements: list[Requirement] = []
        section = "UNSCOPED"
        counter: dict[str, int] = {}
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if line.startswith("## "):
                section = line[3:].strip()
                continue
            if line.startswith("### "):
                section = line[4:].strip()
                continue
            if line.startswith("- "):
                text = line[2:].strip()
                if not text:
                    continue
                slug = _slugify(section)
                counter[slug] = counter.get(slug, 0) + 1
                requirement_id = f"PRD::{slug}::{counter[slug]}"
                requirements.append(Requirement(id=requirement_id, section=section, text=text))
        return cls(requirements)


def _tokenise(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if token}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


__all__ = ["Requirement", "RequirementsCatalog"]

