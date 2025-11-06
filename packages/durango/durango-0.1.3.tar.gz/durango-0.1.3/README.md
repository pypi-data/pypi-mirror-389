[![CI](https://github.com/bryaneburr/durango-config/actions/workflows/ci.yml/badge.svg)](https://github.com/bryaneburr/durango-config/actions/workflows/ci.yml)
![PyPI - Version](https://img.shields.io/pypi/v/durango)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/durango)
![GitHub License](https://img.shields.io/github/license/bryaneburr/durango-config)

# Durango

<img src="https://github.com/bryaneburr/durango-config/raw/main/images/durango_logo.png" height="200" style="height: 200px" />

Durango is a lightweight configuration management toolkit that layers strongly typed settings, configuration files, environment variables, and programmatic overrides using [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). It is designed for CLI tools and services that need predictable precedence, multi-format config files, and clear error reporting.

## Key Features

- **Config precedence**: defaults → config file → environment variables → user overrides.
- **Format flexibility**: parse YAML, JSON, or TOML files by default with optional extras.
- **Typed settings**: describe your configuration with Pydantic models and receive fully validated objects.
- **Reload aware**: refresh configuration at runtime and hook into lifecycle callbacks.
- **Extensible**: adapt environment prefixes, merge behaviour, and file lookup strategies to fit your application.

## Installation

Durango is published on PyPI as `durango`. Install it with your preferred tool:

```bash
# Using uv (recommended)
uv add durango

# Using pip
pip install durango
```

Durango supports Python 3.9 through 3.12.

## Quick Start

```python
from durango import ConfigManager, DurangoSettings


class AppSettings(DurangoSettings):
    debug: bool = False
    api_url: str


manager = ConfigManager(
    settings_type=AppSettings,
    identifier="MYAPP",
    default_file="~/.config/myapp/settings.yaml",
)

settings = manager.load()
print(settings.api_url)
```

If `~/.config/myapp/settings.yaml` does not exist, Durango will create it and populate it with the model defaults before layering environment variables and runtime overrides.

Environment variables take the form `MYAPP__API_URL=true`. To override a nested section named `database`, use `MYAPP__DATABASE__URL`.

## Documentation

- Docs site (WIP): see `docs/`
- Architecture notes: `ARCH.md`
- Working session notes: `notes/STATUS.md`

## Contributing

See [docs/contributing.md](docs/contributing.md) for full setup, workflow, and review guidelines. Highlights:

- Install dependencies with `uv sync --all-extras --dev`.
- Run `uv run invoke ci` before opening a pull request.
- Publishing and release automation are covered in [docs/publishing.md](docs/publishing.md).

## License

Durango is available under the MIT License. See `LICENSE` for details.
