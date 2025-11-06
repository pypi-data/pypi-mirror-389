"""Utilities used across Durango."""

from __future__ import annotations

from .merge import deep_merge_dicts
from .paths import ensure_path, expand_user_path

__all__ = ["deep_merge_dicts", "ensure_path", "expand_user_path"]
