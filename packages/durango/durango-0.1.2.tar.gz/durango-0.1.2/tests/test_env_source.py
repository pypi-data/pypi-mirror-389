"""Tests for environment variable parsing."""

from __future__ import annotations

from durango.sources import build_env_map


def test_build_env_map_nested_keys() -> None:
    environ = {
        "APP__DATABASE__URL": "postgres://localhost",
        "APP__SEARCH__DEFAULT_LIMIT": "10",
        "OTHER": "ignored",
    }

    result = build_env_map("app", environ)

    assert result["database"]["url"] == "postgres://localhost"
    assert result["search"]["default_limit"] == "10"
    assert "OTHER" not in result


def test_build_env_map_normalizes_hyphenated_keys() -> None:
    environ = {"APP__SEARCH-CONFIG__AUTO_ENABLE": "false"}

    result = build_env_map("APP", environ)

    assert result["search_config"]["auto_enable"] == "false"
