from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet

from .constants import (
    DEFAULT_GEMINI_LIVE_API_VERSION,
    DEFAULT_GEMINI_OPENAI_BASE,
    DEFAULT_OPENAI_BASE,
    DEFAULT_OPENROUTER_BASE,
    DEFAULT_ORG_API_BASE,
    DEFAULT_TIMEOUT_SECONDS,
)


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 0.3
    max_delay_seconds: float = 5.0
    retryable_status_codes: FrozenSet[int] = field(
        default_factory=lambda: frozenset({408, 429, 500, 502, 503, 504})
    )


@dataclass(frozen=True)
class OAConfig:
    org_api_base: str = DEFAULT_ORG_API_BASE
    openrouter_api_base: str = DEFAULT_OPENROUTER_BASE
    openai_api_base: str = DEFAULT_OPENAI_BASE
    gemini_openai_api_base: str = DEFAULT_GEMINI_OPENAI_BASE
    gemini_live_api_version: str = DEFAULT_GEMINI_LIVE_API_VERSION
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    retry: RetryConfig = field(default_factory=RetryConfig)
