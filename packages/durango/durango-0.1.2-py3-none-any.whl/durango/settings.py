"""Shared settings base classes for Durango."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class DurangoSettings(BaseSettings):
    """Base class for Durango configuration models.

    Subclass this type to describe application settings that Durango should manage.
    The default configuration rejects unknown fields to highlight typos early and
    defers environment parsing to the `ConfigManager`.
    """

    model_config = SettingsConfigDict(
        extra="forbid",
        frozen=False,
        validate_assignment=False,
    )
