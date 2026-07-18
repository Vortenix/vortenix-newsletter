"""Construct email providers and recipient overrides from local environment values."""

from __future__ import annotations

import os

from vortenix_newsletter.domain.exceptions import ConfigurationError

from .base import EmailProvider
from .console_provider import ConsoleEmailProvider
from .smtp_provider import SMTPEmailProvider


def create_email_provider() -> EmailProvider:
    """Return the configured email provider, defaulting to the safe console adapter."""
    provider = os.getenv("VORTENIX_EMAIL_PROVIDER", "console").strip().casefold()
    if provider == "console":
        return ConsoleEmailProvider()
    if provider == "smtp":
        return SMTPEmailProvider()
    raise ConfigurationError(f"Unsupported VORTENIX_EMAIL_PROVIDER: {provider}")


def configured_recipients(default: list[str]) -> list[str]:
    """Use comma-separated private recipients when configured, otherwise YAML defaults."""
    value = os.getenv("VORTENIX_RECIPIENTS", "")
    recipients = [address.strip() for address in value.split(",") if address.strip()]
    return recipients or default
