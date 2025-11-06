# Contributing to Durango

Durango welcomes improvements from the community. Follow this guide to set up the project locally, keep quality checks passing, and stay aligned with the release workflow.

## Environment Setup

Install the development dependencies (including docs extras) with [uv](https://github.com/astral-sh/uv):

```bash
uv sync --all-extras --dev
uv run pre-commit install
```

If you need to refresh dependencies later, rerun `uv sync --all-extras --dev`.

## Quality Gates

Durango exposes the most common checks as [Invoke](https://www.pyinvoke.org/) tasks. After installation, explore the catalogue with:

```bash
uv run invoke --list
```

Frequently used tasks:

- `uv run invoke ci` — execute Ruff, MyPy, pytest, and MkDocs in one shot.
- `uv run invoke lint --check-format` — ensure Ruff style and auto-fix issues with `--fix`.
- `uv run invoke tests` — run the pytest suite with optional `-m`/`-k` filters.
- `uv run invoke docs-build` — build the documentation site locally (add `--strict` to fail on warnings).
- `uv run invoke docs-serve` — preview the documentation server at `http://127.0.0.1:8000`.

Run the CI task before sending a pull request to match our GitHub workflow.

## Development Workflow

1. Create a feature branch from `main`.
2. Make changes and run the appropriate Invoke tasks.
3. Update relevant documentation under `docs/` and coordination notes in `notes/STATUS.md`.
4. Open a pull request and include context about testing performed.

Refer to [docs/publishing.md](publishing.md) for release-specific automation when preparing a new version.
