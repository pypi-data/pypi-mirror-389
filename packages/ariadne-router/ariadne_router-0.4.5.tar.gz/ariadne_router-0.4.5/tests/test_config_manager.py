"""Tests for the Ariadne configuration system."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ariadne.config.config import (
    AriadneConfig,
    ConfigManager,
    configure_ariadne,
    get_config,
    get_config_manager,
    save_config,
)


@pytest.fixture(autouse=True)
def reset_global_config(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.config.config as config_module

    monkeypatch.setattr(config_module, "_config_manager", None)


def test_ariadne_config_initializes_default_backends() -> None:
    config = AriadneConfig()
    priorities = config.get_backend_priority_list()

    assert priorities[0] == "stim"
    assert "cuda" in config.backends


def test_backend_update_and_serialization_roundtrip() -> None:
    config = AriadneConfig()
    config.update_backend_config("cuda", priority=4, enable_multi_gpu=True, extra_flag=True)

    serialized = config.to_dict()
    restored = AriadneConfig.from_dict(serialized)

    assert restored.backends["cuda"].priority == 4
    assert restored.backends["cuda"].custom_options["extra_flag"] is True


def test_config_manager_load_and_save(tmp_path: Path) -> None:
    config_path = tmp_path / "ariadne.json"
    manager = ConfigManager(config_path)

    manager.config.update_backend_config("stim", priority=11)
    manager.save_config(config_path)

    loaded = json.loads(config_path.read_text())
    assert loaded["backends"]["stim"]["priority"] == 11

    manager.config.update_backend_config("stim", priority=3)
    manager.load_from_file(config_path)
    assert manager.get_backend_config("stim").priority == 11


def test_config_manager_platform_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = ConfigManager(config_file=tmp_path / "config.yaml")

    monkeypatch.setattr(manager, "_detect_platform", lambda: "apple_silicon")
    manager.configure_for_platform("auto")
    assert manager.get_backend_config("metal").enabled is True

    manager.configure_for_platform("nvidia_gpu")
    assert manager.get_backend_config("cuda").enabled is True

    manager.configure_for_platform("cpu_only")
    assert manager.get_backend_config("cuda").enabled is False


def test_create_template_config(tmp_path: Path) -> None:
    manager = ConfigManager(config_file=tmp_path / "config.yaml")
    template_path = tmp_path / "template.yaml"
    manager.create_template_config(template_path)

    text = template_path.read_text()
    assert "stim" in text and "optimization" in text


def test_global_configuration_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "global.yaml"

    monkeypatch.setattr(ConfigManager, "_get_default_config_path", lambda self: config_path)
    configure_ariadne(config_path)

    config = get_config()
    assert isinstance(config, AriadneConfig)

    manager = get_config_manager()
    manager.set_backend_preference("tensor_network", 9)

    assert "tensor_network" in get_config().backends

    save_config(config_path)
    assert config_path.exists()
