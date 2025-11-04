"""Completion provider implementations."""

from __future__ import annotations

from typing import Any

import httpx

from .models import QueueJob
from .worker import CompletionProvider


class OpenRouterCompletionProvider(CompletionProvider):
    """Invoke OpenRouter chat completions for queued jobs."""

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = "https://openrouter.ai/api/v1/chat/completions",
    ) -> None:
        self._api_key = api_key
        self._endpoint = endpoint

    async def complete(self, job: QueueJob) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = {
            "model": job.payload.model,
            "messages": job.payload.messages,
        }
        if job.payload.temperature is not None:
            payload["temperature"] = job.payload.temperature
        if job.payload.max_tokens is not None:
            payload["max_tokens"] = job.payload.max_tokens
        if job.payload.response_format is not None:
            payload["response_format"] = job.payload.response_format
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self._endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://atlas-orchestrator.dev",
                    "X-Title": "Atlas Orchestrator Premium Gateway",
                },
            )
            response.raise_for_status()
            data = response.json()
        messages = data.get("choices", [{}])[0].get("message", {})
        result = {
            "type": "chat.completion",
            "messages": [messages] if messages else [],
        }
        usage = self._build_usage(data.get("usage", {}), data.get("pricing"))
        return result, usage

    def _build_usage(self, usage: dict[str, Any], pricing: Any) -> dict[str, Any]:
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        openrouter_cost = usage.get("total_cost")
        payload: dict[str, Any] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        if pricing is not None:
            payload["pricing"] = pricing
        if openrouter_cost is not None:
            try:
                cost_value = float(openrouter_cost)
            except (TypeError, ValueError):
                cost_value = None
            if cost_value is not None:
                payload["openrouter_cost"] = {
                    "value": f"{cost_value:.6f}",
                    "currency": "USD",
                }
        return payload

