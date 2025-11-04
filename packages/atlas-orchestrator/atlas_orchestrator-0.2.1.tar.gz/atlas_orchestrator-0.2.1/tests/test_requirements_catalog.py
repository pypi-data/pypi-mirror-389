from __future__ import annotations

from atlas_orchestrator.specs.requirements import Requirement, RequirementsCatalog


def test_find_related_matches_keywords() -> None:
    catalog = RequirementsCatalog(
        [
            Requirement(
                id="PRD::analysis::1",
                section="Analysis",
                text="Capture telemetry for new flows",
            ),
            Requirement(id="PRD::design::1", section="Design", text="Define modular boundaries"),
        ]
    )

    related = catalog.find_related(["Telemetry Module", "Boundaries"], limit=None)

    assert {requirement.id for requirement in related} == {
        "PRD::analysis::1",
        "PRD::design::1",
    }


def test_markdown_loader_extracts_sections(tmp_path) -> None:
    doc = tmp_path / "requirements.md"
    doc.write_text(
        """
## Analysis
- Capture telemetry
- Ensure resilience

### Design
- Define APIs
""",
        encoding="utf-8",
    )

    catalog = RequirementsCatalog.from_markdown(doc)
    related = catalog.find_related(["telemetry"])

    assert related and related[0].id.startswith("PRD::analysis")

