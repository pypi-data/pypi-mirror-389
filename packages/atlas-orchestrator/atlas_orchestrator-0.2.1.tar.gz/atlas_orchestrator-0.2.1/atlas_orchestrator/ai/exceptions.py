"""Common exceptions for AI provider integrations."""

from __future__ import annotations

class AIProviderError(RuntimeError):
    """Raised when an AI provider request fails."""

    def __init__(self, provider: str, message: str, *, recoverable: bool = True) -> None:
        self.provider = provider
        self.recoverable = recoverable
        super().__init__(message)


class AIRateLimitError(AIProviderError):
    """Raised when a provider signals rate limiting."""

    def __init__(self, provider: str, message: str = "Rate limit exceeded") -> None:
        super().__init__(provider, message, recoverable=True)


class AINonRetryableError(AIProviderError):
    """Raised when a provider error should stop fallback attempts."""

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(provider, message, recoverable=False)


__all__ = [
    "AIProviderError",
    "AINonRetryableError",
    "AIRateLimitError",
]
