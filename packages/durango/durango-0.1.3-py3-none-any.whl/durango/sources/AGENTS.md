# Sources Module Agents Guide

Handles file, environment, and programmatic override sources.

## Responsibilities

- `file.py`: read/write configuration files and bootstrap defaults.
- `env.py`: translate `<IDENTIFIER>__SECTION__KEY` environment variables into nested dictionaries.
- `user.py`: normalizes override mappings.

## Coordination Notes

- New file formats require updates to serialization, parsing, and associated tests.
- Ensure environment parsing stays deterministic; any delimiter change must be reflected in docs/tests.
- Keep functions pure; side effects (like file creation) should remain within explicit helpers.
