# Durango Config

<img src="img/durango_logo.png" height="100" style="height: 100px"/>

Durango is a configuration toolkit for Python applications that need predictable precedence across files, environment variables, and runtime overrides. It wraps [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) with a focused API that:

- Promotes strongly typed configuration models (`DurangoSettings`).
- Creates missing config files automatically (YAML, JSON, or TOML).
- Resolves configuration in a single place (`ConfigManager`) so CLIs, daemons, and tests share one source of truth.
- Surfaces validation errors early by forbidding unknown keys.

## Installation

Durango is available on PyPI as `durango`. Use whichever installer matches your workflow:

```bash
# Using uv (recommended)
uv add durango

# Using pip
pip install durango
```

Durango targets Python 3.9–3.12.

## Core Concepts

Durango always evaluates configuration in the same order:

1. **Model defaults** – values defined on your `DurangoSettings` subclasses.
2. **Config file** – detected by extension (YAML/JSON/TOML) and created if missing.
3. **Environment variables** – names follow `<IDENTIFIER>__SECTION__KEY`.
4. **Programmatic overrides** – merged last via `load(overrides=...)` or `override(...)`.

Later layers win. Unknown keys in any layer raise a validation error so typos do not slip into production.

## Quick Start

```python
from durango import ConfigManager, DurangoSettings


class ApiSettings(DurangoSettings):
    api_url: str
    token: str
    timeout_seconds: int = 10


manager = ConfigManager(
    settings_type=ApiSettings,
    identifier="MYAPP",
    default_file="~/.config/myapp/config.yaml",
)

settings = manager.load()
```

The first call to `load()` creates `~/.config/myapp/config.yaml` with the defaults above if the file does not exist. You can now set overrides through the file, environment (`MYAPP__TOKEN=...`), or runtime (`manager.override({"timeout_seconds": 5})`).

### Nested Configuration in Practice

Durango handles arbitrarily deep structures, so model your configuration tree directly:

```python
class FeatureFlags(DurangoSettings):
    enable_search: bool = True
    result_limit: int = 10


class ApiSettings(DurangoSettings):
    api_url: str
    token: str
    features: FeatureFlags = FeatureFlags()


settings = ConfigManager(
    settings_type=ApiSettings,
    identifier="MYAPP",
    default_file="~/.config/myapp/config.toml",
).load()
```

Environment variables such as `MYAPP__FEATURES__RESULT_LIMIT=25` or file snippets like:

```toml
[features]
enable_search = false
```

map cleanly onto the nested models while still respecting precedence.

## CLI Integration at a Glance

Durango plays well with CLI frameworks such as [Click](https://click.palletsprojects.com/). Pass command-line options into `load(config_path=...)` or `override(...)` before using the settings. See [Usage Examples](reference/examples.md#cli-with-click) for a ready-to-copy template that wires Durango into a Click command group.

## Common Scenarios

- **Per-environment configuration** – point `default_file` to a team-specific location and let environment variables provide secrets in CI.
- **Nested sections** – compose multiple `DurangoSettings` subclasses; Durango merges arbitrarily deep dictionaries and maps environment variables like `MYAPP__SEARCH__DEFAULT_LIMIT`.
- **Hot reload** – register `"pre_reload"`/`"post_load"` callbacks to reconfigure background workers without restarting.
- **Tests** – inject temporary files by passing `config_path` to `load()` and populate overrides with dictionaries for quick fixtures.

The [Config Manager reference](reference/config-manager.md) walks through each capability in detail.

## Pitfalls & Tips

- `DurangoSettings` uses `extra="forbid"`. Remove stray keys from files or environment variables rather than ignoring them.
- Durango does not silently swallow file errors; `ConfigFileError` includes the offending path and message. Surface the error through your CLI’s JSON or summary output.
- If you need additional serialization formats, extend the file source (see [Architecture](architecture.md)) and register custom loaders.

## What to Read Next

- [Usage Examples](reference/examples.md) – concise recipes for scripts, CLIs, and services.
- [Config Manager](reference/config-manager.md) – constructor options, callback lifecycle, and override mechanics.
- [Settings Models](reference/settings.md) – guidance for shaping nested models and keeping defaults consistent.
- [Architecture](architecture.md) – deeper look at how sources, utilities, and settings interact.
- Maintainers: see [Guides → Contributing](contributing.md) and [Guides → Publishing](publishing.md) for workflow and release automation.
