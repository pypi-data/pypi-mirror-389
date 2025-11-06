# Config Manager

Durango exposes a single entry point—`ConfigManager`—to coordinate configuration sources and provide a ready-to-use settings instance.

```python
from durango import ConfigManager, DurangoSettings
from pathlib import Path


class ServiceSettings(DurangoSettings):
    debug: bool = False
    database_url: str


manager = ConfigManager(
    settings_type=ServiceSettings,
    identifier="SERVICE",
    default_file=Path("~/.config/service/config.toml"),
)

settings = manager.load()
```

The initial `load()` call expands the path, creates the TOML file with defaults if it does not exist, and materialises a validated `ServiceSettings` instance.

## Constructor Arguments

- **`settings_type`** – a concrete subclass of [`DurangoSettings`](settings.md). Use nested models for complex structures.
- **`identifier`** – the environment prefix. `SERVICE__DATABASE_URL` becomes `database_url`. Nested keys use additional `__` segments.
- **`default_file`** – an optional path to use when no explicit path is supplied. Supports `~` and any `pathlib.Path`.
- **`file_formats`** – iterable of format names (`"yaml"`, `"json"`, `"toml"`) to allow. Leave unset to accept all built-ins.
- **`callbacks`** – mapping of event name to an iterable of callables. Supported events: `"post_load"` and `"pre_reload"`.

## Source Precedence

Durango merges sources in the following order:

1. Model defaults from `settings_type`.
2. Configuration file (either `config_path` passed to `load()`/`reload()` or the resolved `default_file`).
3. Environment variables.
4. Programmatic overrides.

Later entries override earlier ones. Durango performs deep merges so nested dictionaries compose naturally.

## Key Methods

### `load(*, config_path=None, overrides=None, environ=None)`

- `config_path` overrides the default file location for a single call.
- `overrides` merges directly into the final result (highest precedence).
- `environ` lets you pass a custom mapping (handy for tests).

Durango caches the resolved settings and reuses them until you call `reload()`.

### `reload(*, config_path=None, environ=None)`

Runs the same pipeline as `load()`, reapplying stored overrides and firing callbacks in the sequence:

1. `"pre_reload"` callbacks (receiving the previous settings instance).
2. New configuration resolution.
3. `"post_load"` callbacks (receiving the new settings).

### `override(overrides)`

Persists additional override values for future `load()`/`reload()` calls. Overrides merge deeply and can be cleared with `clear_overrides()`.

### `register_callback(event, callback)`

Adds a callback after construction. Callbacks should be fast; offload heavy work to background tasks if needed.

### `to_dict()`

Returns the cached settings as a plain dictionary. Raises `RuntimeError` if `load()` has not been called yet.

## Environment Variable Rules

- Names start with the uppercase identifier and `__`. e.g. `SERVICE__FEATURES__CACHE_TTL`.
- Segments are normalised to lowercase snake_case; hyphens become underscores.
- Empty segments are ignored (`SERVICE____TOKEN` is treated as `TOKEN`, but avoid relying on this).
- Unknown keys trigger `ConfigValidationError` because `DurangoSettings` forbids extras.

## File Handling

- Supported extensions: `.yaml`, `.yml`, `.json`, `.toml`.
- Format detection falls back to `format_hint` supplied to the file source.
- When the file is missing, Durango writes a new file with model defaults.
- Parse errors raise `ConfigFileError` showing the path and root cause—propagate the message to users so they can fix invalid syntax.

## Error Types

- **`ConfigFileError`** – raised when a file cannot be read or parsed.
- **`ConfigValidationError`** – wraps the underlying Pydantic `ValidationError`; inspect `.error` for structured details.
- **`UnsupportedFormatError`** – triggered when a file uses an extension outside the allowed set.

## Best Practices

- Pin one `ConfigManager` per settings model and share it across your application (CLI commands, background workers, tests).
- Keep callbacks pure—avoid mutating settings, instead act on derived copies.
- In tests, use temporary directories and `manager.load(config_path=tmp_path / "config.json")` to isolate state.
- When layering manual overrides (e.g., CLI flags), call `manager.override(...)` once after parsing arguments so subsequent reloads keep the overrides.
