"""Unit tests for _parse_pct and _validate_sidecar_step."""

import pytest
from pathlib import Path

from orchestrator.main import _parse_pct, _validate_sidecar_step

# ---------------------------------------------------------------------------
# Helpers / constants shared across _validate_sidecar_step tests
# ---------------------------------------------------------------------------

SEQ = "01"
SLUG = "slug"
FAIL_PREFIX = "review_failed:"
FAIL_SUFFIX = "-review-{n}.md"


def _dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Return (plan_reviews_dir, artifact_dir), both created."""
    plan_reviews_dir = tmp_path / "plan-reviews"
    artifact_dir = tmp_path / "reviews"
    plan_reviews_dir.mkdir(parents=True)
    artifact_dir.mkdir(parents=True)
    return plan_reviews_dir, artifact_dir


def _call(step_value: str, plan_reviews_dir: Path, artifact_dir: Path) -> str:
    return _validate_sidecar_step(
        step_value, SEQ, SLUG, plan_reviews_dir, artifact_dir, FAIL_PREFIX, FAIL_SUFFIX
    )


# ---------------------------------------------------------------------------
# Task 1: Pass-through values that need no artifact
# ---------------------------------------------------------------------------


def test_validate_empty_string_returns_empty(tmp_path):
    """Should return '' when step_value is '' (empty input short-circuits)."""
    prd, art = _dirs(tmp_path)
    assert _call("", prd, art) == ""


def test_validate_planned_returns_planned(tmp_path):
    """Should return 'planned' when step_value is 'planned'."""
    prd, art = _dirs(tmp_path)
    assert _call("planned", prd, art) == "planned"


def test_validate_implemented_returns_implemented(tmp_path):
    """Should return 'implemented' when step_value is 'implemented'."""
    prd, art = _dirs(tmp_path)
    assert _call("implemented", prd, art) == "implemented"


def test_validate_unknown_value_passthrough(tmp_path):
    """Should return 'some_unknown_value' when step_value is unrecognized (pass-through to heuristic)."""
    prd, art = _dirs(tmp_path)
    assert _call("some_unknown_value", prd, art) == "some_unknown_value"


# ---------------------------------------------------------------------------
# Task 2: plan_review_failed:N gated on the plan-review file
# ---------------------------------------------------------------------------


def test_validate_plan_review_failed_file_present(tmp_path):
    """Should return 'plan_review_failed:2' when plan-reviews/01-slug-plan-review-2.md exists."""
    prd, art = _dirs(tmp_path)
    (prd / "01-slug-plan-review-2.md").write_text("some review content")
    assert _call("plan_review_failed:2", prd, art) == "plan_review_failed:2"


def test_validate_plan_review_failed_file_missing(tmp_path):
    """Should return '' when step_value is 'plan_review_failed:2' but the plan-review file is missing."""
    prd, art = _dirs(tmp_path)
    assert _call("plan_review_failed:2", prd, art) == ""


def test_validate_plan_review_failed_malformed_n(tmp_path):
    """Should return '' when step_value is 'plan_review_failed:abc' (malformed N raises ValueError)."""
    prd, art = _dirs(tmp_path)
    assert _call("plan_review_failed:abc", prd, art) == ""


# ---------------------------------------------------------------------------
# Task 3: plan_reviewed requires a passing plan-review file
# ---------------------------------------------------------------------------


def test_validate_plan_reviewed_with_passing_file(tmp_path):
    """Should return 'plan_reviewed' when a plan-review file content ends with PLAN_REVIEW_PASS."""
    prd, art = _dirs(tmp_path)
    (prd / "01-slug-plan-review-1.md").write_text("Some review notes\n\nPLAN_REVIEW_PASS")
    assert _call("plan_reviewed", prd, art) == "plan_reviewed"


def test_validate_plan_reviewed_no_files(tmp_path):
    """Should return '' when step_value is 'plan_reviewed' but no plan-review files exist."""
    prd, art = _dirs(tmp_path)
    assert _call("plan_reviewed", prd, art) == ""


# ---------------------------------------------------------------------------
# Task 4: review_failed:N gated on the review artifact file
# ---------------------------------------------------------------------------


def test_validate_review_failed_file_present(tmp_path):
    """Should return 'review_failed:1' when reviews/01-slug-review-1.md exists."""
    prd, art = _dirs(tmp_path)
    (art / "01-slug-review-1.md").write_text("review content")
    assert _call("review_failed:1", prd, art) == "review_failed:1"


def test_validate_review_failed_file_missing(tmp_path):
    """Should return '' when step_value is 'review_failed:1' but the review file is missing."""
    prd, art = _dirs(tmp_path)
    assert _call("review_failed:1", prd, art) == ""

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
