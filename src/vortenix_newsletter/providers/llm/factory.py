"""Research mode and LLM provider selection."""

from __future__ import annotations

import os

from vortenix_newsletter.domain.exceptions import ConfigurationError

from .base import LLMProvider
from .openai_provider import OpenAIProvider


def research_mode() -> str:
    """Return the configured research mode."""
    mode = os.getenv("VORTENIX_RESEARCH_MODE", "deterministic").strip().casefold()
    if mode not in {"deterministic", "llm"}:
        raise ConfigurationError(f"Unsupported VORTENIX_RESEARCH_MODE: {mode}")
    return mode


def create_llm_provider() -> LLMProvider:
    """Create the optional OpenAI provider without exposing its API key."""
    if not os.getenv("OPENAI_API_KEY"):
        raise ConfigurationError("OPENAI_API_KEY is required for llm research mode")
    return OpenAIProvider()
