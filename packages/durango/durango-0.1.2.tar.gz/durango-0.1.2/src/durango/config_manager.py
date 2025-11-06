"""ConfigManager orchestrates Durango configuration sources."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

from pydantic import ValidationError

from durango.exceptions import ConfigValidationError
from durango.settings import DurangoSettings
from durango.sources import (
    FileSourceConfig,
    UserOverrides,
    build_env_map,
    ensure_config_file,
    load_config_file,
    normalize_overrides,
)
from durango.utils import deep_merge_dicts, ensure_path

SettingsT = TypeVar("SettingsT", bound=DurangoSettings)
Callback = Callable[[SettingsT], None]

_VALID_EVENTS = {"pre_reload", "post_load"}


class ConfigManager(Generic[SettingsT]):
    """Load typed settings from defaults, files, environment variables, and overrides.

    Args:
        settings_type: Concrete subclass of `DurangoSettings`.
        identifier: Prefix used when parsing environment variables.
        default_file: Application-provided default configuration file path.
        file_formats: Optional iterable restricting file formats.
        callbacks: Mapping of lifecycle events to callables.
    """

    def __init__(
        self,
        *,
        settings_type: type[SettingsT],
        identifier: str,
        default_file: str | Path | None = None,
        file_formats: Iterable[str] | None = None,
        callbacks: Mapping[str, Iterable[Callback]] | None = None,
    ) -> None:
        self._settings_type = settings_type
        self._identifier = identifier
        self._file_config = FileSourceConfig(
            default_path=ensure_path(default_file),
            allowed_formats=tuple(file_formats) if file_formats else None,
        )
        self._overrides = UserOverrides()
        self._callbacks: dict[str, list[Callback]] = {
            event: list(funcs) for event, funcs in (callbacks or {}).items()
        }
        for event in self._callbacks:
            if event not in _VALID_EVENTS:
                raise ValueError(f"Unsupported callback event: {event}")
        self._cached_settings: SettingsT | None = None
        self._default_data = self._compute_defaults()

    @property
    def identifier(self) -> str:
        """Return the identifier used for environment variables."""

        return self._identifier

    def load(
        self,
        *,
        config_path: str | Path | None = None,
        overrides: Mapping[str, Any] | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> SettingsT:
        """Load settings respecting Durango precedence rules.

        Args:
            config_path: Optional explicit configuration file path.
            overrides: Programmatic override mapping added before validation.
            environ: Environment mapping used for overrides (defaults to `os.environ`).

        Returns:
            An instance of the configured settings type.
        """

        if overrides is not None:
            normalized = normalize_overrides(overrides)
            self._overrides.merge(normalized)

        data = self._compose_data(config_path=config_path, environ=environ or os.environ)
        try:
            settings = self._settings_type.model_validate(data)
        except ValidationError as exc:
            raise ConfigValidationError(data=data, error=exc) from exc

        self._cached_settings = settings
        self._emit("post_load", settings)
        return settings

    def reload(
        self,
        *,
        config_path: str | Path | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> SettingsT:
        """Reload the configuration using the original overrides."""

        if self._cached_settings is not None:
            self._emit("pre_reload", self._cached_settings)
        return self.load(config_path=config_path, overrides=None, environ=environ)

    def override(self, overrides: Mapping[str, Any]) -> None:
        """Merge overrides and apply them on the next load."""

        normalized = normalize_overrides(overrides)
        self._overrides.merge(normalized)

    def clear_overrides(self) -> None:
        """Remove all programmatic overrides."""

        self._overrides.clear()

    def to_dict(self) -> dict[str, Any]:
        """Return the cached settings as a dictionary."""

        if self._cached_settings is None:
            raise RuntimeError("Configuration has not been loaded yet.")
        return self._cached_settings.model_dump()

    def register_callback(self, event: str, callback: Callback) -> None:
        """Register a lifecycle callback for the given event."""

        if event not in _VALID_EVENTS:
            raise ValueError(f"Unsupported callback event: {event}")
        self._callbacks.setdefault(event, []).append(callback)

    def _compose_data(
        self,
        *,
        config_path: str | Path | None,
        environ: Mapping[str, str],
    ) -> dict[str, Any]:
        file_path = self._file_config.resolve_path(config_path)
        ensure_config_file(file_path, config=self._file_config, data=self._default_data)
        merged = deepcopy(self._default_data)
        file_data = load_config_file(file_path, config=self._file_config)
        merged = deep_merge_dicts(merged, file_data)
        env_data = build_env_map(self._identifier, environ)
        merged = deep_merge_dicts(merged, env_data)
        merged = deep_merge_dicts(merged, self._overrides.values)
        return merged

    def _emit(self, event: str, settings: SettingsT) -> None:
        callbacks = self._callbacks.get(event, [])
        for callback in callbacks:
            callback(settings)

    def _compute_defaults(self) -> dict[str, Any]:
        try:
            defaults = self._settings_type()
        except Exception:  # pylint: disable=broad-except
            return {}
        return defaults.model_dump()
