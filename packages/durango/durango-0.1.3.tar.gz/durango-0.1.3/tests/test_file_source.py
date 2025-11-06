"""Tests for file-based configuration source."""

from __future__ import annotations

from pathlib import Path

import pytest

from durango.exceptions import ConfigFileError, UnsupportedFormatError
from durango.sources import FileSourceConfig, ensure_config_file, load_config_file


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    config = FileSourceConfig()
    data = load_config_file(tmp_path / "missing.json", config=config)
    assert data == {}


def test_unsupported_format_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.ini"
    path.write_text("[section]\nvalue=1\n", encoding="utf-8")
    config = FileSourceConfig()
    with pytest.raises(UnsupportedFormatError):
        load_config_file(path, config=config)


def test_invalid_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json}", encoding="utf-8")
    config = FileSourceConfig()
    with pytest.raises(ConfigFileError):
        load_config_file(path, config=config)


def test_toml_parsing(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('token = "value"\n', encoding="utf-8")
    config = FileSourceConfig()
    data = load_config_file(path, config=config)
    assert data["token"] == "value"


def test_yaml_parsing_merges_documents(tmp_path: Path) -> None:
    pytest.importorskip("ruamel.yaml")

    path = tmp_path / "config.yaml"
    path.write_text("---\nsection:\n  value: 1\n---\nsection:\n  flag: true\n", encoding="utf-8")
    config = FileSourceConfig()
    data = load_config_file(path, config=config)
    assert data["section"]["value"] == 1
    assert data["section"]["flag"] is True


def test_ensure_config_file_creates_json_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    config = FileSourceConfig()
    created = ensure_config_file(path, config=config, data={"token": "value"})

    assert created is True
    data = load_config_file(path, config=config)
    assert data["token"] == "value"

    second_create = ensure_config_file(path, config=config, data={})
    assert second_create is False
