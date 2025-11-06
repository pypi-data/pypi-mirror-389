# Durango Coordination Guide

Durango is a standalone configuration toolkit built on Pydantic Settings. Use this file to stay aligned across agents.

## Primary Directives

- Ship Durango as a reusable package: keep dependencies minimal, support Python 3.9–3.12, and document public APIs with Google-style docstrings.
- Use `uv` + Invoke tasks (`uv run invoke <task>`) for repeatable workflows; extend `tasks.py` when adding new automation so agents stay in sync.
- `ConfigManager` is the only orchestration entry point. All precedence changes, file bootstrap tweaks, or lifecycle hooks must update docs, tests, and the relevant `AGENTS.md` notes.
- Defaults come from settings models, then config files, env vars, and programmatic overrides. Preserve that order and keep file creation idempotent.
- Configuration files must be readable/writable in YAML, JSON, or TOML. When introducing new formats or serializers, coordinate updates in sources/tests/docs.
- Validation is strict (`extra=forbid`). Unknown keys should raise actionable errors surfaced through CLI/JSON payloads.
- Keep helpers pure where possible; ensure new utilities or sources document coordination expectations (`src/durango/**/AGENTS.md`).
- Maintain docs in `docs/` + `notes/`, recording decisions and next steps in `notes/STATUS.md`.
- Prepare releases via feature branches, running `uv run pre-commit run --all-files`, `uv run pytest`, `uv run mypy`, and `uv run mkdocs build --strict` before tagging.
- After Durango reaches PyPI, integrate into dorgy through lazy imports and shared CLI helpers, keeping Chromadb/search state updates consistent.
