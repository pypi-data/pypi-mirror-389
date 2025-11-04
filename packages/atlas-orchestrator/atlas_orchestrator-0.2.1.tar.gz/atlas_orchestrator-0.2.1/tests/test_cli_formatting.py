from __future__ import annotations

from dataclasses import dataclass

from atlas_orchestrator.cli import _format_modules_list, _format_summary_table, _format_usage


def test_format_summary_table_aligns_columns() -> None:
    table = _format_summary_table(
        "Sample Summary",
        [("Alpha", "one"), ("Beta", "two"), ("Gamma", "three")],
    )
    lines = table.splitlines()
    assert lines[0] == "Sample Summary"
    assert lines[3].startswith("Field")
    assert "Alpha" in lines[5]
    assert "Gamma" in lines[7]


def test_format_modules_list_compacts_long_sequences() -> None:
    modules = ["a", "b", "c", "d"]
    result = _format_modules_list(modules)
    assert "4 total" in result
    assert "a, b, c" in result


@dataclass
class _UsageStub:
    model: str
    input_tokens: int
    output_tokens: int
    total_cost: float


def test_format_usage_includes_cost() -> None:
    usage = _UsageStub(model="test-model", input_tokens=10, output_tokens=20, total_cost=0.123456)
    formatted = _format_usage(usage)
    assert "model=test-model" in formatted
    assert "input=10" in formatted
    assert "output=20" in formatted
    assert "cost=$0.123456" in formatted

