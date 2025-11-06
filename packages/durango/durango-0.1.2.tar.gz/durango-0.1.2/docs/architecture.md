# Durango Architecture

Durango delivers configuration data through three core layers:

1. **Settings Models** (`durango.settings`): Subclasses of `DurangoSettings` capture defaults and validation logic.
2. **Sources** (`durango.sources`): A pluggable loader system resolves configuration files, environment variables, and runtime overrides.
3. **Config Manager** (`durango.config_manager`): Coordinates the sources, enforces precedence, surfaces errors, and exposes lifecycle hooks.

## Module Overview

- `durango.config_manager`: Orchestrates load/reload operations, caches the latest model, and emits lifecycle callbacks.
- `durango.settings`: Shared base model and helper mixins for common sections.
- `durango.sources.file`: File discovery, format detection, and parsing logic.
- `durango.sources.env`: `<IDENTIFIER>__SECTION__KEY` parsing, env prefix management, and normalization.
- `durango.sources.user`: Handles programmatic overrides and merging strategies.
- `durango.exceptions`: Consistent error taxonomy surfaced to calling applications.
- `durango.utils.paths`: Helpers for expanding user paths and respecting XDG conventions.

## Precedence Pipeline

```
defaults -> file source -> environment source -> user overrides
```

Each layer builds on the previous one. Components expose pure functions where possible so integrators can swap modules or supply custom loaders (e.g., secrets managers).

## Integration Expectations

- Host applications provide their preferred default config path during manager construction; Durango will create the file with model defaults if it does not exist.
- Components that mutate external systems (like search manifests) should register callbacks through `ConfigManager` to track reloads.
- Extend file or environment sources by adding new helpers under `durango.sources` and composing them inside `ConfigManager` if your deployment has specialised requirements.

Diagrams and deeper explanations will be added as implementation solidifies.
