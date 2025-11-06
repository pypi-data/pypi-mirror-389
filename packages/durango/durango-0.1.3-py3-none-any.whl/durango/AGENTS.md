# Durango Agents Guide

Durango coordinates configuration across multiple consumers. Keep this document updated when coordination expectations evolve.

## Responsibilities

- `ConfigManager` owns precedence resolution, lifecycle callbacks, config file bootstrapping, and error propagation.
- Source modules (`durango.sources.*`) must remain side-effect free aside from optional config creation.
- Utilities (`durango.utils.*`) provide shared helpers for deep merges and path handling; prefer pure functions so other agents can reuse them across modules.

## Coordination Notes

- Defaults are captured from settings models at manager instantiation; changes to `DurangoSettings` subclasses can affect file bootstrapping.
- Adding new lifecycle hooks or altering precedence requires updates here, the docs, and consumer integration guides.
- When expanding supported file formats, update `FileSourceConfig`, serializer helpers, and relevant tests.

## Next Steps for Contributors

- Document custom source extension points and JSON error payload expectations when they change so downstream consumers stay aligned.
- Flesh out docs for multi-level nested settings and environment overrides.
- Prepare release automation for TestPyPI/PyPI once documentation stabilizes.
