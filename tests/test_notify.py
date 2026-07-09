"""Unit tests for notify() — emoji-prefix mapping and telegram gating."""

import pytest

from orchestrator import notify as notify_module
from orchestrator.config import OrchestratorConfig
from orchestrator.notify import notify


def _config(telegram_alerts, bot_token="t", chat_id="c") -> OrchestratorConfig:
    return OrchestratorConfig(
        max_iterations=3,
        usage_threshold_5h=90,
        usage_threshold_weekly=95,
        enable_phase_sessions=False,
        telegram_bot_token=bot_token,
        telegram_chat_id=chat_id,
        telegram_alerts=telegram_alerts,
    )


@pytest.fixture
def sent(monkeypatch):
    """Monkeypatch send_telegram with a recorder; never hits the network."""
    recorded = []

    def _fake_send_telegram(token, chat_id, text):
        recorded.append(text)

    monkeypatch.setattr(notify_module, "send_telegram", _fake_send_telegram)
    return recorded


# ---------------------------------------------------------------------------
# Task 1: Emoji-prefix mapping
# ---------------------------------------------------------------------------

ALL_ALERTS = ["stop", "halt", "milestone", "done", "whatever"]


def test_stop_alert_prefixed_red(sent):
    """Should prefix the message with 🔴 for alert_type 'stop'."""
    config = _config(ALL_ALERTS)
    notify(config, "some message", "stop")
    assert sent[0].startswith("🔴")


def test_halt_alert_prefixed_yellow(sent):
    """Should prefix the message with 🟡 for alert_type 'halt' (red now — current code has no _HALT_ALERTS)."""
    config = _config(ALL_ALERTS)
    notify(config, "some message", "halt")
    assert sent[0].startswith("🟡")


def test_milestone_alert_prefixed_green(sent):
    """Should prefix the message with 🟢 for alert_type 'milestone'."""
    config = _config(ALL_ALERTS)
    notify(config, "some message", "milestone")
    assert sent[0].startswith("🟢")


def test_done_alert_prefixed_green(sent):
    """Should prefix the message with 🟢 for alert_type 'done'."""
    config = _config(ALL_ALERTS)
    notify(config, "some message", "done")
    assert sent[0].startswith("🟢")


def test_unknown_alert_prefixed_green(sent):
    """Should prefix the message with 🟢 for an unrecognized alert_type 'whatever'."""
    config = _config(ALL_ALERTS)
    notify(config, "some message", "whatever")
    assert sent[0].startswith("🟢")


# ---------------------------------------------------------------------------
# Task 2: Gating (silent no-op)
# ---------------------------------------------------------------------------


def test_alert_type_not_listed_sends_nothing(sent):
    """Should send nothing when alert_type is not present in config.telegram_alerts."""
    config = _config(["milestone"])
    notify(config, "some message", "stop")
    assert sent == []


def test_missing_bot_token_sends_nothing(sent):
    """Should send nothing when telegram_bot_token is None, even though alert_type is listed and chat_id is set."""
    config = _config(["stop"], bot_token=None)
    notify(config, "some message", "stop")
    assert sent == []


def test_missing_chat_id_sends_nothing(sent):
    """Should send nothing when telegram_chat_id is None, even though alert_type is listed and token is set."""
    config = _config(["stop"], chat_id=None)
    notify(config, "some message", "stop")
    assert sent == []
