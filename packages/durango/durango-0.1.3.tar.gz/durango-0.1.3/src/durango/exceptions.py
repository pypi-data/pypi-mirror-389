"""Durango-specific exception hierarchy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError


class DurangoError(RuntimeError):
    """Base class for all Durango errors."""


class ConfigFileError(DurangoError):
    """Raised when configuration files cannot be read or parsed."""

    def __init__(self, *, path: Path, message: str, cause: Exception | None = None) -> None:
        self.path = path
        self.message = message
        self.cause = cause
        detail = f"{message} (path={path})"
        if cause:
            detail = f"{detail}: {cause}"
        super().__init__(detail)


class ConfigValidationError(DurangoError):
    """Raised when Pydantic validation fails for the settings model."""

    def __init__(self, *, data: dict[str, Any], error: ValidationError) -> None:
        self.data = data
        self.error = error
        message = "; ".join(err["msg"] for err in error.errors())
        super().__init__(f"Configuration validation failed: {message}")


class UnsupportedFormatError(DurangoError):
    """Raised when a configuration file uses an unsupported format."""

    def __init__(self, *, path: Path, format_name: str) -> None:
        self.path = path
        self.format_name = format_name
        super().__init__(f"Unsupported configuration format '{format_name}' for {path}")
