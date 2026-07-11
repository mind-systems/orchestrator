"""Unit tests for _run_summary formatting."""

import time

from orchestrator import state
from orchestrator.runtime import _run_summary


def test_run_summary_with_elapsed_and_count():
    """Should append the ' · N milestones done' suffix when run_started is set."""
    saved_started, saved_done = state.run_started, state.milestones_done
    try:
        state.run_started = time.monotonic() - 5
        state.milestones_done = 3
        result = _run_summary()
        assert result.startswith("Ran for ")
        assert result.endswith(" · 3 milestones done")
    finally:
        state.run_started, state.milestones_done = saved_started, saved_done


def test_run_summary_with_no_run_started():
    """Should read exactly 'Ran for unknown · 0 milestones done' when run_started is None."""
    saved_started, saved_done = state.run_started, state.milestones_done
    try:
        state.run_started = None
        state.milestones_done = 0
        assert _run_summary() == "Ran for unknown · 0 milestones done"
    finally:
        state.run_started, state.milestones_done = saved_started, saved_done
