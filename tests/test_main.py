"""Unit tests for _parse_pct, _validate_sidecar_step, _detect_milestone_step, and _detect_test_milestone_step."""

import json
import subprocess
import sys

import pytest
from pathlib import Path

from orchestrator import agents as agents_module
from orchestrator import main as main_module
from orchestrator.agents import PipelineStopError, RateLimitError
from orchestrator.config import OrchestratorConfig
from orchestrator.main import (
    _check_usage_limits,
    _detect_milestone_step,
    _detect_test_milestone_step,
    _parse_pct,
    _validate_sidecar_step,
    process_milestone,
)

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


# ---------------------------------------------------------------------------
# _detect_milestone_step tests
# ---------------------------------------------------------------------------

DMS_SEQ = "01"
DMS_SLUG = "slug"


def _dms_dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build .ai-factory/{plans,plan-reviews,reviews} and return (plan_reviews_dir, reviews_dir, plan_path).

    plan_path points to plans/01-slug.md (not created — caller decides whether to write it).
    """
    plans_dir = tmp_path / ".ai-factory" / "plans"
    plan_reviews_dir = tmp_path / ".ai-factory" / "plan-reviews"
    reviews_dir = tmp_path / ".ai-factory" / "reviews"
    plans_dir.mkdir(parents=True)
    plan_reviews_dir.mkdir(parents=True)
    reviews_dir.mkdir(parents=True)
    plan_path = plans_dir / f"{DMS_SEQ}-{DMS_SLUG}.md"
    return plan_reviews_dir, reviews_dir, plan_path


# ---------------------------------------------------------------------------
# Task 1: Fresh start and sidecar-driven steps (no git repo needed)
# ---------------------------------------------------------------------------


def test_detect_milestone_step_no_plan_file_returns_plan(tmp_path):
    """Should return ("plan", 1, plan_path) when the plan file does not exist."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    # plan_path intentionally not created on disk
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "plan"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_milestone_step_sidecar_planned_returns_plan_review(tmp_path):
    """Should return ("plan_review", 1, plan_path) when sidecar step is "planned"."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "planned"}))
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "plan_review"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_milestone_step_sidecar_implemented_returns_review(tmp_path):
    """Should return ("review", 1, plan_path) when sidecar step is "implemented"."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "implemented"}))
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "review"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_milestone_step_sidecar_review_failed_returns_implement(tmp_path):
    """Should return ("implement", 2, plan_path) when sidecar step is "review_failed:1" and reviews/01-slug-review-1.md is present."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "review_failed:1"}))
    (rv / f"{DMS_SEQ}-{DMS_SLUG}-review-1.md").write_text("review content")
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "implement"
    assert counter == 2
    assert returned_path == plan_path


# ---------------------------------------------------------------------------
# Task 2: Clean-working-tree branch (git fixture genuinely required)
# ---------------------------------------------------------------------------


def test_detect_milestone_step_clean_tree_no_sidecar_passing_plan_review_returns_implement(tmp_path):
    """Should return ("implement", 1, plan_path) when no sidecar step, a passing plan-review is present, and the working tree is clean."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    # No sidecar JSON — _read_sessions returns {}
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    # Init git repo with an empty commit so `git diff HEAD` works
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # .ai-factory/ artifacts are excluded by :!.ai-factory → both git commands return empty stdout
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "implement"
    assert counter == 1
    assert returned_path == plan_path


# ---------------------------------------------------------------------------
# Task 3: Canonical slug/seq resolution on mismatch
# ---------------------------------------------------------------------------


def test_detect_milestone_step_canonical_path_resolution(tmp_path):
    """Should resolve canonical plan path to 01-slug.md and return ("plan_review", 1, that path) when caller passes seq="02" and plan_path=02-slug.md."""
    prd, rv, plan_path_01 = _dms_dirs(tmp_path)
    plan_path_01.write_text("# Plan content")
    # Only 01-slug.md exists; 02-slug.md does not
    plans_dir = plan_path_01.parent
    plan_path_02 = plans_dir / "02-slug.md"
    # No sidecar, no plan-review files → falls through to "plan_review"
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, "02", DMS_SLUG, plan_path_02, prd, rv
    )
    assert step == "plan_review"
    assert counter == 1
    assert returned_path == plan_path_01


# ---------------------------------------------------------------------------
# _detect_test_milestone_step tests
# ---------------------------------------------------------------------------

DTMS_SEQ = "01"
DTMS_SLUG = "slug"


def _dtms_dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build .ai-factory/{plans,plan-reviews,test-runs} and return (plan_reviews_dir, test_runs_dir, plan_path).

    plan_path points to plans/01-slug.md (not created — caller decides whether to write it).
    """
    plans_dir = tmp_path / ".ai-factory" / "plans"
    plan_reviews_dir = tmp_path / ".ai-factory" / "plan-reviews"
    test_runs_dir = tmp_path / ".ai-factory" / "test-runs"
    plans_dir.mkdir(parents=True)
    plan_reviews_dir.mkdir(parents=True)
    test_runs_dir.mkdir(parents=True)
    plan_path = plans_dir / f"{DTMS_SEQ}-{DTMS_SLUG}.md"
    return plan_reviews_dir, test_runs_dir, plan_path


# ---------------------------------------------------------------------------
# Task 1: Fresh start and sidecar-driven steps (no git repo needed)
# ---------------------------------------------------------------------------


def test_detect_test_milestone_step_no_plan_file_returns_plan(tmp_path):
    """Should return ("plan", 1, plan_path) when the plan file does not exist."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    # plan_path intentionally not created on disk
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "plan"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_test_milestone_step_sidecar_plan_reviewed_returns_implement(tmp_path):
    """Should return ("implement", 1, plan_path) when sidecar step is "plan_reviewed" and a passing plan-review file is present."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "plan_reviewed"}))
    (prd / f"{DTMS_SEQ}-{DTMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "implement"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_test_milestone_step_sidecar_implemented_returns_test_run(tmp_path):
    """Should return ("test_run", 1, plan_path) when sidecar step is "implemented"."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "implemented"}))
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "test_run"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_test_milestone_step_sidecar_test_run_failed_returns_implement(tmp_path):
    """Should return ("implement", 2, plan_path) when sidecar step is "test_run_failed:1" and test-runs/01-slug-test-1.txt is present."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "test_run_failed:1"}))
    (trd / f"{DTMS_SEQ}-{DTMS_SLUG}-test-1.txt").write_text("test output")
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "implement"
    assert counter == 2
    assert returned_path == plan_path


# ---------------------------------------------------------------------------
# Task 2: Heuristic fall-through reaching test-run artifacts (git fixture required)
# ---------------------------------------------------------------------------


def test_detect_test_milestone_step_dirty_tree_passing_test_run_returns_done(tmp_path):
    """Should return ("done", 0, plan_path) when no sidecar step, a passing plan-review is present, the working tree is dirty, and the latest test-runs/01-slug-test-1.txt ends with TEST_PASS."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    # No sidecar JSON → _read_sessions returns {}
    (prd / f"{DTMS_SEQ}-{DTMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    (trd / f"{DTMS_SEQ}-{DTMS_SLUG}-test-1.txt").write_text("Test output\n\nTEST_PASS")
    # Init git repo with an empty commit so `git diff HEAD` works
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # Create an untracked file outside .ai-factory to make the working tree dirty
    (tmp_path / "src.py").write_text("x = 1\n")
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "done"
    assert counter == 0
    assert returned_path == plan_path


# ---------------------------------------------------------------------------
# cli() exception-routing tests
# ---------------------------------------------------------------------------


def _cli_config() -> OrchestratorConfig:
    return OrchestratorConfig(
        max_iterations=3,
        usage_threshold_5h=90,
        usage_threshold_weekly=95,
        enable_phase_sessions=False,
    )


def _run_cli_with(monkeypatch, exc):
    """Patch load_config/run_implement/notify/argv; return the list notify() calls get recorded into."""
    recorded = []

    monkeypatch.setattr(main_module, "load_config", lambda: _cli_config())

    def _raise_run_implement(project_dir, config):
        raise exc

    monkeypatch.setattr(main_module, "run_implement", _raise_run_implement)

    def _fake_notify(config, text, alert_type):
        recorded.append((text, alert_type))

    monkeypatch.setattr(main_module, "notify", _fake_notify)
    monkeypatch.setattr(sys, "argv", ["orchestrator", "implement", "."])
    return recorded


def test_cli_pipeline_stop_error_routes_to_stop(monkeypatch):
    """Should record alert_type 'stop' and exit via SystemExit when run_implement raises PipelineStopError."""
    recorded = _run_cli_with(monkeypatch, PipelineStopError("boom"))
    with pytest.raises(SystemExit):
        main_module.cli()
    assert recorded[-1][1] == "stop"


def test_cli_rate_limit_error_routes_to_halt(monkeypatch):
    """Should record alert_type 'halt' when run_implement raises RateLimitError (red now — currently routes to 'stop')."""
    recorded = _run_cli_with(monkeypatch, RateLimitError("boom"))
    with pytest.raises(SystemExit):
        main_module.cli()
    assert recorded[-1][1] == "halt"


def test_cli_generic_exception_routes_to_halt_and_reraises(monkeypatch):
    """Should record alert_type 'halt' and re-raise a generic Exception (red now — cli() has no except Exception today)."""
    recorded = _run_cli_with(monkeypatch, ValueError("boom"))
    with pytest.raises(ValueError):
        main_module.cli()
    assert recorded and recorded[-1][1] == "halt"


# ---------------------------------------------------------------------------
# Source-level exception-type tests: both currently raise PipelineStopError,
# both should raise HaltError once task 05 lands.
# ---------------------------------------------------------------------------


def test_check_usage_limits_raises_halt_error_over_threshold(monkeypatch):
    """Should raise HaltError when session usage crosses usage_threshold_5h (red now — currently raises PipelineStopError)."""
    config = OrchestratorConfig(
        max_iterations=3,
        usage_threshold_5h=90,
        usage_threshold_weekly=95,
        enable_phase_sessions=False,
    )

    class _Result:
        stdout = "Current session: 99%"

    monkeypatch.setattr(main_module.subprocess, "run", lambda *a, **kw: _Result())

    with pytest.raises(Exception) as exc:
        _check_usage_limits(config)

    HaltError = getattr(agents_module, "HaltError", None)
    assert HaltError is not None and isinstance(exc.value, HaltError)


def test_process_milestone_resume_past_max_iterations_raises_halt_error(tmp_path):
    """Should raise HaltError when resuming at an iteration beyond max_iterations (red now — currently raises PipelineStopError)."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "review_failed:3"}))
    (rv / f"{DMS_SEQ}-{DMS_SLUG}-review-3.md").write_text("review content")
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )

    config = OrchestratorConfig(
        max_iterations=3,
        usage_threshold_5h=90,
        usage_threshold_weekly=95,
        enable_phase_sessions=False,
    )

    class _MilestoneStub:
        slug = DMS_SLUG
        title = "Some milestone"
        description = "Some description"
        line_number = 0

    with pytest.raises(Exception) as exc:
        process_milestone(tmp_path, _MilestoneStub(), 1, config)

    HaltError = getattr(agents_module, "HaltError", None)
    assert HaltError is not None and isinstance(exc.value, HaltError)
