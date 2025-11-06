# Usage Examples

This page showcases common ways to integrate Durango into real projects. Each example is intentionally short and highlights the surrounding context so you can adapt it quickly.

## Basic Script

```python
from durango import ConfigManager, DurangoSettings


class AppSettings(DurangoSettings):
    api_url: str
    timeout_seconds: int = 10


settings = ConfigManager(
    settings_type=AppSettings,
    identifier="APP",
    default_file="~/.config/app/settings.yaml",
).load()

print(settings.api_url)
```

Durango will create `~/.config/app/settings.yaml` if it does not exist, seeding it with the model defaults before layering environment variables and overrides.

## CLI with Click

```python
import click
from durango import ConfigManager, DurangoSettings


class ServiceSettings(DurangoSettings):
    endpoint: str
    debug: bool = False


manager = ConfigManager(
    settings_type=ServiceSettings,
    identifier="SERVICE",
    default_file="~/.service/config.toml",
)


@click.group()
@click.option("--config", type=click.Path(), help="Override config file path.")
@click.pass_context
def cli(ctx: click.Context, config: str | None) -> None:
    settings = manager.load(config_path=config)
    ctx.obj = {"settings": settings}


@cli.command()
@click.pass_context
def ping(ctx: click.Context) -> None:
    settings: ServiceSettings = ctx.obj["settings"]
    click.echo(f"Pinging {settings.endpoint} (debug={settings.debug})")


if __name__ == "__main__":
    cli()
```

Key details:

- Command-line options can override the path before the first `load()` call.
- Extra CLI flags map cleanly to `manager.override(...)` if you want to promote runtime changes to highest precedence.

## Environment Overrides

Environment variables use the `<IDENTIFIER>__SECTION__KEY` pattern. Nested sections become additional segments.

```bash
export SERVICE__ENDPOINT="https://api.example.com"
export SERVICE__FEATURES__CACHE_TTL=300
```

Pair this with settings that match the shape:

```python
class FeatureSettings(DurangoSettings):
    cache_ttl: int = 120


class ServiceSettings(DurangoSettings):
    endpoint: str
    features: FeatureSettings = FeatureSettings()
```

Durango normalises dashed names to snake_case (`SERVICE__FEATURES__CACHE-TTL` → `features.cache_ttl`) and forbids unknown keys so typos surface immediately.

## Hot Reload with Callbacks

Long-running services can observe configuration changes via callbacks.

```python
from durango import ConfigManager, DurangoSettings


class SearchSettings(DurangoSettings):
    default_limit: int = 20


def on_post_load(settings: SearchSettings) -> None:
    print("Loaded search settings:", settings.model_dump())


manager = ConfigManager(
    settings_type=SearchSettings,
    identifier="SEARCH",
    default_file="~/.search/config.json",
    callbacks={"post_load": [on_post_load]},
)


settings = manager.load()
# Later, maybe on a signal:
manager.reload()
```

Callbacks fire on the main thread; keep them fast and delegate heavy work to background tasks if necessary.

## Merging Runtime Overrides

Use `manager.override()` to capture programmatic configuration that sits above environment variables and files. This is ideal for CLI flags or UI-driven options.

```python
manager.override({"features": {"enable_metrics": True}})
settings = manager.reload()
```

Durango performs deep merges, so you can override a single nested value without rewriting the entire section.
