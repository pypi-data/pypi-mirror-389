# Durango Status Log

## 2025-02-15 — Session Notes

- Documented the expanded Invoke release workflow (build, publish, bump-version, tag-version, release) powered by uv.
- Updated README/docs to describe new flags (`--index-url`, `--skip-existing`, `--dry-run`) and token handling expectations.
- Broke out contributing and publishing guides into dedicated docs pages and added them to the MkDocs navigation.
- Next: fill in remaining release metadata (long description URLs, project homepage) before first upload.

## 2025-11-04 — Session Notes

- Scaffolded new Durango package with tooling, docs skeleton, and CI workflow.
- Implemented core modules (config manager, sources, utils, exceptions) plus Google-style docstrings.
- Added pytest coverage for precedence, environment parsing, and file loaders; `uv run pytest` passing.
- Adjusted precedence to anchor on model defaults, added automatic config file creation, and scrubbed repository-specific references.
- Added AGENTS guides for config, sources, and utilities modules.
- Next session: extend documentation, finalize release metadata, and draft publishing workflow.
