"""User-supplied override handling."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any

from durango.utils import deep_merge_dicts


@dataclass
class UserOverrides:
    """Container for programmatic override values."""

    values: dict[str, Any] = field(default_factory=dict)

    def merge(self, overrides: Mapping[str, Any]) -> None:
        """Merge new overrides into the container."""

        self.values = deep_merge_dicts(self.values, overrides)

    def clear(self) -> None:
        """Remove all override values."""

        self.values.clear()


def normalize_overrides(overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize a mapping of overrides.

    Args:
        overrides: Raw mapping supplied by the caller.

    Returns:
        A deep-copied dictionary suitable for merging.
    """

    if overrides is None:
        return {}
    if isinstance(overrides, MutableMapping):
        # Use dict() to avoid preserving custom mapping subclasses.
        return deep_merge_dicts({}, overrides)
    return deep_merge_dicts({}, dict(overrides))
