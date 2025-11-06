# Publishing Durango

Durango’s release workflow is driven by Invoke tasks that wrap the `uv` command-line interface. This guide captures the recommended sequence for dry runs, TestPyPI verification, and production releases.

## Pre-flight Checklist

1. Ensure `main` (or your release branch) includes the changes you intend to publish.
2. Run the full quality gate:

   ```bash
   uv run invoke ci
   ```

3. Confirm the changelog or release notes capture user-facing changes.

## Inspect Available Tasks

List the release-related Invoke tasks:

```bash
uv run invoke --list
```

Key tasks:

- `build` — generate wheel and sdist artifacts (use `--clean` to delete `dist/` before building).
- `publish` — upload artifacts to a package index (`--index-url`, `--skip-existing`, `--dry-run`, `--token` supported).
- `bump-version` — update `pyproject.toml` using semantic version bumps or explicit values.
- `tag-version` — create annotated git tags and optionally push them to `origin`.
- `release` — orchestrate the entire workflow (version bump → build → publish → tag).

## Dry Runs and TestPyPI

Always validate the workflow before touching the production index:

```bash
uv run invoke build
uv run invoke publish --index-url https://test.pypi.org/simple/ --skip-existing --dry-run
uv run invoke release --dry-run
```

Dry runs echo the commands so you can verify options, environment variables, and resolved versions.

## Production Releases

Set a PyPI token in the environment (it will be echoed when passed as a CLI flag):

```bash
export PYPI_API_TOKEN="pypi-..."
```

Then execute the release steps:

```bash
uv run invoke bump-version --part patch
uv run invoke build --clean
uv run invoke publish --token "$PYPI_API_TOKEN"
uv run invoke tag-version --push
```

Alternatively, let the `release` task manage the sequence:

```bash
uv run invoke release --token "$PYPI_API_TOKEN" --push-tag
```

### Optional Flags

- `--index-url https://test.pypi.org/simple/` — target TestPyPI for smoke testing.
- `--skip-existing` — avoid re-uploading artifacts already present on the index.
- `--dry-run` — print commands without executing them.
- `--part major|minor|patch` or `--value 1.2.3` — control version bumps.
- `--tag-prefix ""` — create tags without the default `v` prefix.

## Post-release

1. Push or merge the release branch once the publish step succeeds.
2. Draft GitHub release notes referencing the generated tag.
3. Update any dependent projects (e.g., dorgy) to consume the new version.
