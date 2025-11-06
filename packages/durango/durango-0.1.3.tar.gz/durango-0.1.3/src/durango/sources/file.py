"""File-based configuration sources."""

from __future__ import annotations

import io
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from durango.exceptions import ConfigFileError, UnsupportedFormatError
from durango.utils import deep_merge_dicts, ensure_path

_YAML_EXTENSIONS = {"yaml", "yml"}
_JSON_EXTENSIONS = {"json"}
_TOML_EXTENSIONS = {"toml"}


@dataclass(frozen=True)
class FileSourceConfig:
    """Configuration for the file source.

    Attributes:
        default_path: The preferred configuration file path supplied by the host.
        allowed_formats: Optional list of format names (e.g., `["yaml", "json"]`).
    """

    default_path: Path | None = None
    allowed_formats: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.allowed_formats is not None:
            canonical = tuple({_canonical_format(fmt) for fmt in self.allowed_formats})
            object.__setattr__(self, "allowed_formats", canonical)

    def resolve_path(self, override: str | Path | None) -> Path | None:
        """Resolve a caller supplied path or fall back to the default."""

        return ensure_path(override) or self.default_path

    def is_allowed(self, format_name: str) -> bool:
        """Check whether a format is allowed by this configuration."""

        if self.allowed_formats is None:
            return True
        return _canonical_format(format_name) in self.allowed_formats


def load_config_file(
    path: Path | None,
    *,
    config: FileSourceConfig,
    format_hint: str | None = None,
) -> dict[str, Any]:
    """Load configuration data from a file if it exists.

    Args:
        path: The configuration file path. If `None`, the function returns an empty mapping.
        config: Runtime options for the file loader.
        format_hint: Explicit format name overriding file extension detection.

    Returns:
        A dictionary containing the parsed configuration values.

    Raises:
        UnsupportedFormatError: If the file extension is not supported.
        ConfigFileError: If the file cannot be read or parsed.
    """

    if path is None:
        return {}
    resolved = path.expanduser()
    if not resolved.exists():
        return {}

    format_name = _detect_format(resolved, format_hint=format_hint)
    if not config.is_allowed(format_name):
        raise UnsupportedFormatError(path=resolved, format_name=format_name)

    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigFileError(
            path=resolved,
            message="Unable to read configuration file",
            cause=exc,
        ) from exc

    try:
        data = _parse_text(text, format_name=format_name, path=resolved)
    except UnsupportedFormatError:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise ConfigFileError(
            path=resolved,
            message="Failed to parse configuration file",
            cause=exc,
        ) from exc

    if data is None:
        return {}
    if not isinstance(data, Mapping):
        raise ConfigFileError(
            path=resolved,
            message=f"Expected mapping at document root, received {type(data).__name__}",
            cause=None,
        )
    return dict(data)


def ensure_config_file(
    path: Path | None,
    *,
    config: FileSourceConfig,
    data: Mapping[str, Any],
    format_hint: str | None = None,
) -> bool:
    """Create a configuration file with defaults when missing.

    Args:
        path: The target configuration file path.
        config: File source configuration ensuring format compatibility.
        data: Defaults to serialize when creating the file.
        format_hint: Optional explicit format when the path lacks an extension.

    Returns:
        `True` if a file was created, otherwise `False`.
    """

    if path is None:
        return False
    resolved = path.expanduser()
    if resolved.exists():
        return False

    format_name = _detect_format(resolved, format_hint=format_hint)
    if not config.is_allowed(format_name):
        raise UnsupportedFormatError(path=resolved, format_name=format_name)

    try:
        text = _dump_text(dict(data), format_name=format_name, path=resolved)
    except UnsupportedFormatError:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise ConfigFileError(
            path=resolved,
            message="Failed to serialize default configuration",
            cause=exc,
        ) from exc

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ConfigFileError(
            path=resolved,
            message="Unable to write configuration file",
            cause=exc,
        ) from exc

    return True


def _detect_format(path: Path, *, format_hint: str | None) -> str:
    if format_hint:
        return _canonical_format(format_hint)
    suffix = path.suffix.lower().lstrip(".")
    if suffix:
        return _canonical_format(suffix)
    raise UnsupportedFormatError(path=path, format_name="unknown")


def _canonical_format(format_name: str) -> str:
    lowered = format_name.lower()
    if lowered in _YAML_EXTENSIONS:
        return "yaml"
    if lowered in _JSON_EXTENSIONS:
        return "json"
    if lowered in _TOML_EXTENSIONS:
        return "toml"
    return lowered


def _parse_text(text: str, *, format_name: str, path: Path) -> dict[str, Any]:
    format_name = format_name.lower()
    if format_name in _YAML_EXTENSIONS:
        return _load_yaml(text, path=path)
    if format_name in _JSON_EXTENSIONS:
        return _load_json(text, path=path)
    if format_name in _TOML_EXTENSIONS:
        return _load_toml(text, path=path)
    raise UnsupportedFormatError(path=path, format_name=format_name)


def _load_yaml(text: str, *, path: Path) -> dict[str, Any]:
    try:
        from ruamel.yaml import YAML
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise UnsupportedFormatError(path=path, format_name="yaml") from exc

    yaml = YAML(typ="safe")
    documents = [doc for doc in yaml.load_all(text) if doc is not None]
    if not documents:
        return {}

    merged: dict[str, Any] = {}
    for document in documents:
        if not isinstance(document, Mapping):
            raise ValueError("YAML configuration documents must be mappings")
        merged = deep_merge_dicts(merged, document)
    return merged


def _load_json(text: str, *, path: Path) -> dict[str, Any]:
    import json

    data = json.loads(text)
    if not isinstance(data, Mapping):
        raise ValueError(f"JSON configuration must be an object at the root ({path})")
    return dict(data)


def _dump_text(data: Mapping[str, Any], *, format_name: str, path: Path) -> str:
    format_name = format_name.lower()
    if format_name in _YAML_EXTENSIONS:
        return _dump_yaml(data, path=path)
    if format_name in _JSON_EXTENSIONS:
        return _dump_json(data)
    if format_name in _TOML_EXTENSIONS:
        return _dump_toml(data, path=path)
    raise UnsupportedFormatError(path=path, format_name=format_name)


def _dump_yaml(data: Mapping[str, Any], *, path: Path) -> str:
    try:
        from ruamel.yaml import YAML
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise UnsupportedFormatError(path=path, format_name="yaml") from exc

    yaml = YAML()
    yaml.default_flow_style = False
    buffer = io.StringIO()
    yaml.dump(dict(data), buffer)
    return buffer.getvalue()


def _dump_json(data: Mapping[str, Any]) -> str:
    import json

    return json.dumps(data, indent=2, sort_keys=True)


def _dump_toml(data: Mapping[str, Any], *, path: Path) -> str:
    try:
        return _toml_from_mapping(data)
    except Exception as exc:  # pylint: disable=broad-except
        raise ConfigFileError(
            path=path,
            message="Failed to serialize TOML configuration",
            cause=exc,
        ) from exc


def _toml_from_mapping(data: Mapping[str, Any]) -> str:
    lines: list[str] = []

    def write_table(prefix: str, table: Mapping[str, Any]) -> None:
        scalars: dict[str, Any] = {}
        subtables: dict[str, Mapping[str, Any]] = {}

        for key, value in table.items():
            if isinstance(value, Mapping):
                subtables[key] = value
            else:
                scalars[key] = value

        if prefix:
            lines.append(f"[{prefix}]")

        for key, value in scalars.items():
            lines.append(f"{key} = {_render_toml_value(value)}")

        if scalars:
            lines.append("")

        for key, value in subtables.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            write_table(child_prefix, value)

    write_table("", data)

    # Remove trailing blank lines.
    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def _render_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        return "[" + ", ".join(_render_toml_value(item) for item in value) + "]"
    if isinstance(value, Mapping):
        raise ValueError("Nested mappings are handled separately")
    if value is None:
        return '""'
    return f'"{str(value)}"'


def _load_toml(text: str, *, path: Path) -> dict[str, Any]:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
        import tomli as tomllib

    data = tomllib.loads(text)
    if not isinstance(data, Mapping):
        raise ValueError(f"TOML configuration must be a table at the root ({path})")
    return dict(data)
