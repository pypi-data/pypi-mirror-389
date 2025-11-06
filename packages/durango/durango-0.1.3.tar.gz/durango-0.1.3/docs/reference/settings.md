# Settings Models

`DurangoSettings` extends `pydantic_settings.BaseSettings` with configuration tuned for Durango:

- `extra="forbid"` so unexpected keys fail fast.
- Assignment validation is disabled so you can mutate fields at runtime if desired.
- No `env_prefix`; `ConfigManager` handles prefixing uniformly.

```python
from durango import DurangoSettings


class SearchSettings(DurangoSettings):
    default_limit: int = 20
    auto_enable: bool = True
    embedding_function: str = "text-embedding-3-small"
```

## Defaults & Validation

- Provide rich types (`HttpUrl`, enums, dataclasses) and defaults for happy-path behaviour.
- Use `model_config = SettingsConfigDict(frozen=True)` if you want immutable settings instances.
- For optional values, prefer `Field(default=None)` to document intent.
- Validation errors propagate as `ConfigValidationError`; include descriptions in field metadata to help callers.

## Nested Structures

Durango merges dictionaries recursively, so nest additional `DurangoSettings` (or Pydantic `BaseModel`) subclasses to mirror complex configuration trees.

```python
from pydantic import Field


class DatabaseSettings(DurangoSettings):
    url: str
    pool_size: int = 5


class AppSettings(DurangoSettings):
    debug: bool = False
    database: DatabaseSettings = DatabaseSettings(
        url="postgres://localhost/db",
        pool_size=10,
    )
    feature_flags: dict[str, bool] = Field(default_factory=dict)
```

Environment variables such as `APP__DATABASE__POOL_SIZE=20` map directly to nested attributes.

## Secrets & External Stores

Durango intentionally keeps secrets in whichever layer you prefer:

- Use environment variables for volatile secrets (`APP__TOKEN`).
- Pull from secret managers in a `"post_load"` callback and merge them via `manager.override(...)`.

Avoid storing secrets in the generated config file unless you control file permissions carefully.

## Testing Patterns

- Build lightweight fixtures by instantiating settings directly: `AppSettings(token="test-token")`.
- For integration tests, point `ConfigManager` at a temporary directory and pass overrides to seed deterministic values.

## Helpful Modules

- `durango.settings` – base class definition.
- `durango.sources.file` – file parsing and format support.
- `durango.sources.env` – environment variable normalisation logic.

Refer to the [Usage Examples](examples.md) page for end-to-end snippets that combine these pieces.
