"""Unit tests for _has_signal."""

import pytest

from orchestrator.agents import _has_signal


# ---------------------------------------------------------------------------
# Task 1: match within the last-5-line window
# ---------------------------------------------------------------------------


def test_signal_on_last_line():
    """Signal is the exact last line — most common case."""
    text = "some preamble\nmore text\nREVIEW_PASS"
    assert _has_signal(text, "REVIEW_PASS") is True


def test_signal_on_line_3_of_5():
    """Signal is on line 3 of 5: still inside the last-5 window."""
    lines = ["line1", "line2", "REVIEW_PASS", "line4", "line5"]
    assert _has_signal("\n".join(lines), "REVIEW_PASS") is True


def test_signal_on_line_6_of_10():
    """Signal is the first line inside the last-5 window of a 10-line text."""
    # Lines 1-5 (indices 0-4) are outside [-5:]; line 6 (index 5) is first inside.
    lines = [
        "line1", "line2", "line3", "line4", "line5",
        "REVIEW_PASS",  # index 5 — first line of [-5:]
        "line7", "line8", "line9", "line10",
    ]
    assert _has_signal("\n".join(lines), "REVIEW_PASS") is True


def test_signal_is_plan_review_pass():
    """Function is signal-agnostic: PLAN_REVIEW_PASS works the same way."""
    text = "planning notes\nPLAN_REVIEW_PASS"
    assert _has_signal(text, "PLAN_REVIEW_PASS") is True


# ---------------------------------------------------------------------------
# Task 2: window exclusion and exact-match rejection
# ---------------------------------------------------------------------------


def test_signal_on_line_5_of_10_excluded():
    """Signal is on line 5 (index 4) of a 10-line text — just outside [-5:]."""
    lines = [
        "line1", "line2", "line3", "line4",
        "REVIEW_PASS",  # index 4 — excluded by [-5:]
        "line6", "line7", "line8", "line9", "line10",
    ]
    assert _has_signal("\n".join(lines), "REVIEW_PASS") is False


def test_signal_as_substring_rejected():
    """Signal embedded in a longer line must NOT match (strip+equality check)."""
    text = "some text\nno REVIEW_PASS here\nmore text"
    assert _has_signal(text, "REVIEW_PASS") is False


def test_signal_with_surrounding_whitespace():
    """A line with leading/trailing whitespace still matches after strip()."""
    text = "preamble\n  REVIEW_PASS  \ntrailer"
    assert _has_signal(text, "REVIEW_PASS") is True


def test_empty_text_returns_false():
    """Empty string has no lines; any() over an empty iterable is False."""
    assert _has_signal("", "REVIEW_PASS") is False
