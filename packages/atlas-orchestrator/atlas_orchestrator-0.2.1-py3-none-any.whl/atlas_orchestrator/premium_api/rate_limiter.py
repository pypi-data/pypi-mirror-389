import asyncio
import time
from dataclasses import dataclass, field as dataclass_field
from typing import Protocol

try:  # pragma: no cover - optional dependency import guard
    from redis.asyncio import Redis  # type: ignore
except Exception:  # pragma: no cover - redis optional
    Redis = None  # type: ignore


class RateLimiter(Protocol):
    """Interface for quota enforcement strategies."""

    async def allow(self, identifier: str, *, per_minute: int, burst: int) -> bool:  # pragma: no cover
        raise NotImplementedError


@dataclass
class InMemoryRateLimiter(RateLimiter):
    """Process-local token bucket implementation."""

    _lock: asyncio.Lock = dataclass_field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self._state: dict[str, tuple[float, float]] = {}

    async def allow(self, identifier: str, *, per_minute: int, burst: int) -> bool:
        async with self._lock:
            now = time.monotonic()
            tokens, last = self._state.get(identifier, (float(burst), now))
            elapsed = max(0.0, now - last)
            refill = (per_minute / 60.0) * elapsed
            tokens = min(float(burst), tokens + refill)
            if tokens < 1.0:
                self._state[identifier] = (tokens, now)
                return False
            tokens -= 1.0
            self._state[identifier] = (tokens, now)
            return True


class RedisRateLimiter(RateLimiter):
    """Redis-backed token bucket rate limiter."""

    _LUA = """
    local key = KEYS[1]
    local rate = tonumber(ARGV[1])
    local burst = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local ttl = tonumber(ARGV[4])
    local state = redis.call('HMGET', key, 'tokens', 'timestamp')
    local tokens = tonumber(state[1])
    local timestamp = tonumber(state[2])
    if tokens == nil then
        tokens = burst
        timestamp = now
    end
    local delta = math.max(0, now - timestamp)
    tokens = math.min(burst, tokens + delta * rate / 60)
    if tokens < 1 then
        redis.call('HMSET', key, 'tokens', tokens, 'timestamp', now)
        redis.call('PEXPIRE', key, ttl)
        return 0
    end
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'timestamp', now)
    redis.call('PEXPIRE', key, ttl)
    return 1
    """

    def __init__(self, client: "Redis") -> None:
        if client is None:  # pragma: no cover - guard for missing redis dependency
            raise RuntimeError("redis library is not installed")
        self._client = client
        self._script = client.register_script(self._LUA)

    async def allow(self, identifier: str, *, per_minute: int, burst: int) -> bool:
        now = time.time()
        ttl_ms = int(max(10.0, 120.0 * 1000))
        result = await self._script(keys=[f"rate:{identifier}"], args=[per_minute, burst, now, ttl_ms])
        return bool(result)
