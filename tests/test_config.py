"""Unit tests for OrchestratorConfig.roadmap_path loading and its load-time guard."""

import json

import pytest

from orchestrator.config import load_config

REQUIRED_FIELDS = {
    "max_iterations": 3,
    "usage_threshold_5h": 90,
    "usage_threshold_weekly": 95,
    "enable_phase_sessions": False,
}


def _write_config(tmp_path, monkeypatch, extra=None):
    data = dict(REQUIRED_FIELDS)
    if extra:
        data.update(extra)
    config_path = tmp_path / "orchestrator.json"
    config_path.write_text(json.dumps(data))
    monkeypatch.setenv("ORCHESTRATOR_CONFIG", str(config_path))
    return config_path


def test_load_config_absent_roadmap_path_is_none(tmp_path, monkeypatch):
    """Should set roadmap_path to None when the key is absent."""
    _write_config(tmp_path, monkeypatch)
    config = load_config()
    assert config.roadmap_path is None


def test_load_config_roadmap_path_passes_through(tmp_path, monkeypatch):
    """Should pass an explicit relative roadmap_path value through verbatim."""
    _write_config(tmp_path, monkeypatch, {"roadmap_path": "roadmaps/alice.md"})
    config = load_config()
    assert config.roadmap_path == "roadmaps/alice.md"


def test_load_config_roadmap_path_my_passes_through(tmp_path, monkeypatch):
    """Should pass the literal 'my' value through verbatim (resolution happens elsewhere)."""
    _write_config(tmp_path, monkeypatch, {"roadmap_path": "my"})
    config = load_config()
    assert config.roadmap_path == "my"


def test_load_config_roadmap_path_absolute_raises_system_exit(tmp_path, monkeypatch):
    """Should raise SystemExit naming the offending value when roadmap_path is absolute."""
    _write_config(tmp_path, monkeypatch, {"roadmap_path": "/etc/passwd"})
    with pytest.raises(SystemExit) as exc:
        load_config()
    assert "/etc/passwd" in str(exc.value)


def test_load_config_roadmap_path_dotdot_raises_system_exit(tmp_path, monkeypatch):
    """Should raise SystemExit naming the offending value when roadmap_path contains a '..' segment."""
    _write_config(tmp_path, monkeypatch, {"roadmap_path": "../evil.md"})
    with pytest.raises(SystemExit) as exc:
        load_config()
    assert "../evil.md" in str(exc.value)
