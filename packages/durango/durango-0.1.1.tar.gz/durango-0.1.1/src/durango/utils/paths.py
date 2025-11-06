"""Path helpers for Durango."""

from __future__ import annotations

from pathlib import Path


def expand_user_path(path: str | Path) -> Path:
    """Expand user and environment variables within a path string.

    Args:
        path: A filesystem path that may include `~` or environment variables.

    Returns:
        A resolved `Path` object without attempting to access the filesystem.
    """

    return Path(str(path)).expanduser()


def ensure_path(path: str | Path | None) -> Path | None:
    """Normalize optional path values.

    Args:
        path: A string or `Path` value or `None`.

    Returns:
        `None` if no path is provided, otherwise an expanded `Path`.
    """

    if path is None:
        return None
    return expand_user_path(path)
