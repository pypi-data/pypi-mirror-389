"""ConfigManager integration tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from durango import ConfigManager, DurangoSettings
from durango.exceptions import ConfigValidationError


class NestedSettings(DurangoSettings):
    """Nested section used for precedence tests."""

    value: int = 0
    flag: bool = False


class ExampleSettings(DurangoSettings):
    """Example settings used across tests."""

    section: NestedSettings = NestedSettings()
    token: str = "unset"
    mode: str = "default"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    import json

    path.write_text(json.dumps(payload), encoding="utf-8")


def test_config_manager_precedence(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_json(
        config_path,
        {
            "section": {"value": 1, "flag": False},
            "token": "from-file",
        },
    )

    manager = ConfigManager(
        settings_type=ExampleSettings,
        identifier="APP",
        default_file=config_path,
    )

    environ = {"APP__SECTION__VALUE": "5", "APP__MODE": "env"}
    overrides = {"token": "override-token"}

    settings = manager.load(environ=environ, overrides=overrides)

    assert settings.section.value == 5  # env overrides file
    assert settings.token == "override-token"  # user overrides highest precedence
    assert settings.mode == "env"

    snapshot = manager.to_dict()
    assert snapshot["section"]["value"] == 5


def test_reload_triggers_callbacks(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_json(config_path, {"token": "first"})

    manager = ConfigManager(
        settings_type=ExampleSettings,
        identifier="APP",
        default_file=config_path,
    )

    events: list[str] = []

    def on_post_load(settings: ExampleSettings) -> None:
        events.append(f"post:{settings.token}")

    def on_pre_reload(settings: ExampleSettings) -> None:
        events.append(f"pre:{settings.token}")

    manager.register_callback("post_load", on_post_load)
    manager.register_callback("pre_reload", on_pre_reload)

    manager.load()
    write_json(config_path, {"token": "second"})
    manager.reload()

    assert events == ["post:first", "pre:first", "post:second"]


def test_validation_errors_are_wrapped(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_json(config_path, {"section": {"value": "not-an-int"}})

    manager = ConfigManager(
        settings_type=ExampleSettings,
        identifier="APP",
        default_file=config_path,
    )

    with pytest.raises(ConfigValidationError) as excinfo:
        manager.load()

    message = str(excinfo.value)
    assert "valid integer" in message
    assert excinfo.value.data["section"]["value"] == "not-an-int"


def test_missing_config_file_is_created_with_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    manager = ConfigManager(
        settings_type=ExampleSettings,
        identifier="APP",
        default_file=config_path,
    )

    settings = manager.load()

    assert settings.token == "unset"
    assert config_path.exists()

    import json

    file_data = json.loads(config_path.read_text(encoding="utf-8"))
    assert file_data["section"]["value"] == 0
    assert file_data["token"] == "unset"
