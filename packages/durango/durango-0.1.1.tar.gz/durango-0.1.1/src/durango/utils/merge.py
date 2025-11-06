"""Dictionary merge helpers."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def deep_merge_dicts(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Merge two mappings recursively without mutating inputs.

    Args:
        base: The original mapping.
        overrides: Values that should take precedence.

    Returns:
        A new dictionary representing `base` updated with `overrides`.
    """

    result: dict[str, Any] = deepcopy(dict(base))
    for key, value in overrides.items():
        if key in result and isinstance(result[key], Mapping) and isinstance(value, Mapping):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
