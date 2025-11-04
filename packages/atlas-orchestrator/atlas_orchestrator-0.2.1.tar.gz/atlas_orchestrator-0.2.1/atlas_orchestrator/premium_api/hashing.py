"""Hashing utilities for API keys."""

from __future__ import annotations

from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class KeyHasher:
    """Abstract interface for hashing and verifying API keys."""

    def hash(self, value: str) -> str:  # pragma: no cover - interface only
        raise NotImplementedError

    def verify(self, value: str, hashed: str) -> bool:  # pragma: no cover - interface only
        raise NotImplementedError


@dataclass
class Argon2KeyHasher(KeyHasher):
    """Argon2id-backed hasher suitable for API key storage."""

    time_cost: int = 3
    memory_cost: int = 64 * 1024
    parallelism: int = 2
    hash_len: int = 32

    def __post_init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            hash_len=self.hash_len,
        )

    def hash(self, value: str) -> str:
        return self._hasher.hash(value)

    def verify(self, value: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, value)
        except VerifyMismatchError:
            return False

    def needs_rehash(self, hashed: str) -> bool:
        return self._hasher.check_needs_rehash(hashed)
