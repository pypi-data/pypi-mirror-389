# Config Module Agents Guide

This directory provides configuration models and helpers that other modules depend on.

## Scope

- Keep shared settings models or mixins here when multiple subsystems need them.
- Avoid importing heavy dependencies at module import time; let callers opt in.

## Coordination

- When adding new settings models, document how they map to config files, env vars, and overrides.
- Update `DurangoSettings` docstrings and docs if defaults or validation rules change.
