"""LLM usage estimation helpers."""

from __future__ import annotations

from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field

_DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "gpt-4.1-mini": {"prompt": 0.0005, "completion": 0.0015},
    "openai/gpt-5": {"prompt": 0.01, "completion": 0.03},
}


class LLMUsage(BaseModel):
    """Represents approximate usage and cost for an LLM invocation."""

    model_config = ConfigDict(extra="forbid")

    model: str = Field(description="Resolved model identifier")
    input_tokens: int = Field(ge=0, description="Approximate prompt tokens consumed")
    output_tokens: int = Field(ge=0, description="Approximate completion tokens produced")
    input_cost: float = Field(ge=0.0, description="Estimated prompt cost in USD")
    output_cost: float = Field(ge=0.0, description="Estimated completion cost in USD")
    total_cost: float = Field(ge=0.0, description="Combined prompt and completion cost")


def default_pricing_for(model: str) -> dict[str, float] | None:
    pricing = _DEFAULT_PRICING.get(model)
    if pricing is None:
        return None
    return dict(pricing)



def estimate_usage(
    *,
    model: str,
    prompt_text: str,
    completion_text: str,
    pricing: Mapping[str, float] | None = None,
) -> LLMUsage:
    """Estimate token counts and USD cost using coarse heuristics."""

    prompt_tokens = _approximate_tokens(prompt_text)
    completion_tokens = _approximate_tokens(completion_text)
    resolved_pricing = _resolve_pricing(model, pricing)
    prompt_cost = (prompt_tokens / 1000) * resolved_pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * resolved_pricing["completion"]
    return LLMUsage(
        model=model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        input_cost=round(prompt_cost, 6),
        output_cost=round(completion_cost, 6),
        total_cost=round(prompt_cost + completion_cost, 6),
    )


def _approximate_tokens(text: str) -> int:
    if not text:
        return 0
    # Rough heuristic: assume 4 characters per token and clamp >=1 if text exists
    estimate = max(1, len(text) // 4)
    return estimate


def _resolve_pricing(model: str, pricing: Mapping[str, float] | None) -> dict[str, float]:
    if pricing:
        prompt = float(pricing.get("prompt", 0.0))
        completion = float(pricing.get("completion", 0.0))
        if prompt or completion:
            return {"prompt": prompt, "completion": completion}
    return _DEFAULT_PRICING.get(model, {"prompt": 0.0, "completion": 0.0})


__all__ = ["LLMUsage", "estimate_usage", "default_pricing_for"]
