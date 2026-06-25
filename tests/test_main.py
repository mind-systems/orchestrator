"""Unit tests for _parse_pct."""

import pytest

from orchestrator.main import _parse_pct

# Production patterns verbatim from main.py
SESSION_PATTERN = r"Current session:\s+(\d+(?:\.\d+)?)%"
WEEKLY_PATTERN = r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%"


# ---------------------------------------------------------------------------
# Task 1: Successful matches return the captured percentage as a float
# ---------------------------------------------------------------------------


def test_session_pattern_integer_percentage():
    """Should return 85.0 when session pattern matches 'Current session: 85%'."""
    result = _parse_pct("Current session: 85%", SESSION_PATTERN)
    assert result == 85.0


def test_weekly_pattern_decimal_percentage():
    """Should return 42.5 when weekly pattern matches 'Current week (all models): 42.5%'."""
    result = _parse_pct("Current week (all models): 42.5%", WEEKLY_PATTERN)
    assert result == 42.5


def test_session_pattern_decimal_percentage():
    """Should return 12.3 when session pattern matches a decimal 'Current session: 12.3%'."""
    result = _parse_pct("Current session: 12.3%", SESSION_PATTERN)
    assert result == 12.3


def test_successful_match_returns_float_instance():
    """Should return a float instance (not a string) on a successful match."""
    result = _parse_pct("Current session: 50%", SESSION_PATTERN)
    assert isinstance(result, float)


# ---------------------------------------------------------------------------
# Task 2: Non-matching input returns None
# ---------------------------------------------------------------------------


def test_no_match_unrelated_text():
    """Should return None when session pattern finds no match in unrelated text."""
    result = _parse_pct("No usage data available.", SESSION_PATTERN)
    assert result is None


def test_no_match_unrelated_digits():
    """Should return None when text contains unrelated digits 'used 5 tokens' and does not match the session pattern."""
    result = _parse_pct("used 5 tokens today", SESSION_PATTERN)
    assert result is None


# ---------------------------------------------------------------------------
# Task 3: re.search scans the whole string, returning the first match anywhere
# ---------------------------------------------------------------------------


def test_multiline_returns_first_match():
    """Should return the first matching percentage when given a multi-line output string."""
    text = (
        "Claude Code usage\n"
        "Some other metric: 99\n"
        "Current session: 70%\n"
        "Current week (all models): 30%\n"
    )
    result = _parse_pct(text, SESSION_PATTERN)
    assert result == 70.0
