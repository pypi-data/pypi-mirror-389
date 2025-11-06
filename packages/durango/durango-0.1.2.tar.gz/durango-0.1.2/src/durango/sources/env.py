"""Environment variable configuration source."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

SegmentNormalizer = Callable[[str], str]


def build_env_map(
    identifier: str,
    environ: Mapping[str, str],
    *,
    delimiter: str = "__",
    normalizer: SegmentNormalizer | None = None,
) -> dict[str, Any]:
    """Build a nested mapping from environment variables.

    Args:
        identifier: The environment prefix (e.g., ``"MYAPP"``).
        environ: Environment values, typically `os.environ`.
        delimiter: Separator splitting nested keys.
        normalizer: Callable that normalizes each key segment.

    Returns:
        A nested dictionary derived from matching environment variables.
    """

    normalizer = normalizer or _default_normalizer
    prefix = f"{identifier.upper()}{delimiter}"
    result: dict[str, Any] = {}

    for env_key, value in environ.items():
        if not env_key.upper().startswith(prefix):
            continue
        tail = env_key[len(prefix) :]
        if not tail:
            continue
        segments = [normalizer(part) for part in tail.split(delimiter) if part]
        if not segments:
            continue
        cursor = result
        for segment in segments[:-1]:
            cursor = cursor.setdefault(segment, {})
        cursor[segments[-1]] = value
    return result


def _default_normalizer(segment: str) -> str:
    """Normalize environment segments to snake_case."""

    return segment.strip().lower().replace("-", "_")
