"""Unit tests for _parse_pct, _validate_sidecar_step, _detect_milestone_step, and _detect_test_milestone_step."""

import json
import subprocess
import sys

import pytest
from pathlib import Path

from orchestrator import agents as agents_module
from orchestrator import main as main_module
from orchestrator import usage as usage_module
from orchestrator.agents import HaltError, PipelineStopError, RateLimitError
from orchestrator.config import OrchestratorConfig
from orchestrator.main import (
    _artifact_subdir,
    _derive_identity_slug,
    _next_number,
    _resolve_roadmap_relpath,
    _tests_sibling,
    process_milestone,
)
from orchestrator.resume import (
    _detect_milestone_step,
    _detect_test_milestone_step,
    _validate_sidecar_step,
)
from orchestrator.usage import _check_usage_limits, _parse_pct

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


def _init_dirty_git_repo(tmp_path: Path) -> None:
    """Init a git repo with an empty commit, then dirty the tree with an untracked file outside .ai-factory/."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    (tmp_path / "src.py").write_text("x = 1\n")


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


def test_detect_milestone_step_sidecar_plan_review_failed_returns_plan(tmp_path):
    """Should return ("plan", 3, plan_path) when sidecar step is "plan_review_failed:2" and plan-reviews/01-slug-plan-review-2.md is present."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "plan_review_failed:2"}))
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-2.md").write_text("review content")
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "plan"
    assert counter == 3
    assert returned_path == plan_path


def test_detect_milestone_step_sidecar_plan_reviewed_returns_implement(tmp_path):
    """Should return ("implement", 1, plan_path) when sidecar step is "plan_reviewed" and a passing plan-review file is present."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "plan_reviewed"}))
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "implement"
    assert counter == 1
    assert returned_path == plan_path


# ---------------------------------------------------------------------------
# Heuristic non-git fall-through: latest plan-review not passing
# ---------------------------------------------------------------------------


def test_detect_milestone_step_plan_review_not_passing_returns_plan(tmp_path):
    """Should return ("plan", 2, plan_path) when no sidecar step and the latest plan-review does not end with PLAN_REVIEW_PASS (no git needed — returns before the git diff/status calls)."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text("Review notes, not passing")
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "plan"
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
# Task 3: Heuristic git-dependent branches (dirty-tree path)
# ---------------------------------------------------------------------------


def test_detect_milestone_step_dirty_tree_no_review_files_returns_review(tmp_path):
    """Should return ("review", 1, plan_path) when the plan-review passed, the working tree is dirty, and no review files exist yet."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    _init_dirty_git_repo(tmp_path)
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "review"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_milestone_step_dirty_tree_review_not_passing_returns_implement(tmp_path):
    """Should return ("implement", 2, plan_path) when the plan-review passed, the working tree is dirty, and the latest review does not end with REVIEW_PASS."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    (rv / f"{DMS_SEQ}-{DMS_SLUG}-review-1.md").write_text("Review notes, not passing")
    _init_dirty_git_repo(tmp_path)
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "implement"
    assert counter == 2
    assert returned_path == plan_path


def test_detect_milestone_step_dirty_tree_review_passing_returns_done(tmp_path):
    """Should return ("done", 0, plan_path) when the plan-review passed, the working tree is dirty, and the latest review ends with REVIEW_PASS."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    (rv / f"{DMS_SEQ}-{DMS_SLUG}-review-1.md").write_text("Review notes\n\nREVIEW_PASS")
    _init_dirty_git_repo(tmp_path)
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "done"
    assert counter == 0
    assert returned_path == plan_path

# ---------------------------------------------------------------------------
# Resume adoption gate: tracked+clean plans are stale and skipped;
# only in-flight (untracked/modified/staged) plans are adoptable.
# ---------------------------------------------------------------------------


def test_detect_milestone_step_committed_clean_plan_is_skipped(tmp_path):
    """A tracked+clean plan (committed milestone) must not be adopted, even when the
    heuristic would otherwise resolve it all the way to "done"."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DMS_SEQ}-{DMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    (rv / f"{DMS_SEQ}-{DMS_SLUG}-review-1.md").write_text("Review notes\n\nREVIEW_PASS")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(["git", "add", str(plan_path)], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "-m", "commit plan",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # Dirty the tree outside .ai-factory/, mirroring the in-flight heuristic path that would
    # otherwise be reached if this stale plan were (wrongly) adopted.
    (tmp_path / "src.py").write_text("x = 1\n")
    fresh_seq = "02"
    fresh_plan_path = plan_path.parent / f"{fresh_seq}-{DMS_SLUG}.md"
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, fresh_seq, DMS_SLUG, fresh_plan_path, prd, rv
    )
    assert step == "plan"
    assert counter == 1
    assert returned_path != plan_path
    assert returned_path == fresh_plan_path


def test_detect_milestone_step_untracked_plan_is_adopted(tmp_path):
    """An untracked plan (no commit yet) is in-flight and must be adopted, resuming per
    today's behavior."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "planned"}))
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # plan_path intentionally left untracked
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "plan_review"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_milestone_step_staged_plan_is_adopted(tmp_path):
    """A staged-but-uncommitted plan is in-flight and must be adopted, resuming per today's
    behavior."""
    prd, rv, plan_path = _dms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "planned"}))
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(["git", "add", str(plan_path)], cwd=tmp_path, check=True, capture_output=True)
    # plan_path staged but not committed
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, prd, rv
    )
    assert step == "plan_review"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_milestone_step_survivor_over_lowest(tmp_path):
    """When a lower-seq slug match is committed+clean and a higher-seq slug match is in-flight,
    the higher (survivor) candidate is adopted — not the lowest-overall."""
    prd, rv, plan_path_01 = _dms_dirs(tmp_path)
    plan_path_01.write_text("# Plan content v1")
    plans_dir = plan_path_01.parent
    plan_path_02 = plans_dir / "02-slug.md"
    plan_path_02.write_text("# Plan content v2")
    plan_path_02.with_suffix(".json").write_text(json.dumps({"step": "planned"}))
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(["git", "add", str(plan_path_01)], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "-m", "commit plan 01",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # plan_path_02 intentionally left untracked (in-flight survivor)
    fresh_seq = "03"
    fresh_plan_path = plans_dir / f"{fresh_seq}-{DMS_SLUG}.md"
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, fresh_seq, DMS_SLUG, fresh_plan_path, prd, rv
    )
    assert step == "plan_review"
    assert counter == 1
    assert returned_path == plan_path_02


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


def test_detect_test_milestone_step_sidecar_planned_returns_plan_review(tmp_path):
    """Should return ("plan_review", 1, plan_path) when sidecar step is "planned"."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "planned"}))
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "plan_review"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_test_milestone_step_sidecar_plan_review_failed_returns_plan(tmp_path):
    """Should return ("plan", 3, plan_path) when sidecar step is "plan_review_failed:2" and plan-reviews/01-slug-plan-review-2.md is present."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "plan_review_failed:2"}))
    (prd / f"{DTMS_SEQ}-{DTMS_SLUG}-plan-review-2.md").write_text("review content")
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "plan"
    assert counter == 3
    assert returned_path == plan_path


# ---------------------------------------------------------------------------
# Heuristic non-git fall-through branches (no git needed)
# ---------------------------------------------------------------------------


def test_detect_test_milestone_step_no_plan_review_files_returns_plan_review(tmp_path):
    """Should return ("plan_review", 1, plan_path) when no sidecar step and no plan-review files exist (no git needed — returns before the git diff/status calls)."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "plan_review"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_test_milestone_step_plan_review_not_passing_returns_plan(tmp_path):
    """Should return ("plan", 2, plan_path) when no sidecar step and the latest plan-review does not end with PLAN_REVIEW_PASS."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DTMS_SEQ}-{DTMS_SLUG}-plan-review-1.md").write_text("Review notes, not passing")
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "plan"
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


def test_detect_test_milestone_step_clean_tree_returns_implement(tmp_path):
    """Should return ("implement", 1, plan_path) when no sidecar step, a passing plan-review is present, and the working tree is clean."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DTMS_SEQ}-{DTMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [
            "git", "-c", "user.email=t@t.com", "-c", "user.name=T",
            "commit", "--allow-empty", "-m", "init",
        ],
        cwd=tmp_path, check=True, capture_output=True,
    )
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "implement"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_test_milestone_step_dirty_tree_no_test_run_files_returns_test_run(tmp_path):
    """Should return ("test_run", 1, plan_path) when the plan-review passed, the working tree is dirty, and no test-run files exist yet."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DTMS_SEQ}-{DTMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    _init_dirty_git_repo(tmp_path)
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "test_run"
    assert counter == 1
    assert returned_path == plan_path


def test_detect_test_milestone_step_dirty_tree_test_run_not_passing_returns_implement(tmp_path):
    """Should return ("implement", 2, plan_path) when the plan-review passed, the working tree is dirty, and the latest test-run does not end with TEST_PASS."""
    prd, trd, plan_path = _dtms_dirs(tmp_path)
    plan_path.write_text("# Plan content")
    (prd / f"{DTMS_SEQ}-{DTMS_SLUG}-plan-review-1.md").write_text(
        "Review notes\n\nPLAN_REVIEW_PASS"
    )
    (trd / f"{DTMS_SEQ}-{DTMS_SLUG}-test-1.txt").write_text("Test output, not passing")
    _init_dirty_git_repo(tmp_path)
    step, counter, returned_path = _detect_test_milestone_step(
        tmp_path, DTMS_SEQ, DTMS_SLUG, plan_path, prd, trd
    )
    assert step == "implement"
    assert counter == 2
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

    monkeypatch.setattr(main_module, "load_config", lambda project_dir=None: _cli_config())

    def _raise_run_implement(project_dir, config):
        raise exc

    monkeypatch.setattr(main_module, "run_implement", _raise_run_implement)

    def _fake_notify(config, text, alert_type):
        recorded.append((text, alert_type))

    monkeypatch.setattr(main_module, "notify", _fake_notify)
    monkeypatch.setattr(sys, "argv", ["orchestrator", "implement", "."])
    return recorded


def test_cli_pipeline_stop_error_routes_to_milestone_fail(monkeypatch):
    """Should record alert_type 'milestone-fail' and exit via SystemExit when run_implement raises PipelineStopError."""
    recorded = _run_cli_with(monkeypatch, PipelineStopError("boom"))
    with pytest.raises(SystemExit):
        main_module.cli()
    assert recorded[-1][1] == "milestone-fail"


def test_cli_rate_limit_error_routes_to_stop(monkeypatch):
    """Should record alert_type 'stop' when run_implement raises RateLimitError."""
    recorded = _run_cli_with(monkeypatch, RateLimitError("boom"))
    with pytest.raises(SystemExit):
        main_module.cli()
    assert recorded[-1][1] == "stop"


def test_cli_generic_exception_routes_to_stop_and_reraises(monkeypatch):
    """Should record alert_type 'stop' and re-raise a generic Exception."""
    recorded = _run_cli_with(monkeypatch, ValueError("boom"))
    with pytest.raises(ValueError):
        main_module.cli()
    assert recorded and recorded[-1][1] == "stop"


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

    monkeypatch.setattr(usage_module.subprocess, "run", lambda *a, **kw: _Result())

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


# ---------------------------------------------------------------------------
# _derive_identity_slug: pure slug derivation from git identity
# ---------------------------------------------------------------------------


def test_derive_identity_slug_canonical_example():
    """Should slugify the email local-part per the spec's canonical example."""
    assert _derive_identity_slug("john.doe@example.com", None) == "john-doe"


def test_derive_identity_slug_punctuation_runs_collapse():
    """Should collapse a run of non-alphanumeric characters to a single hyphen."""
    assert _derive_identity_slug("a..b__c@example.com", None) == "a-b-c"


def test_derive_identity_slug_empty_email_falls_back_to_name():
    """Should slugify name when email is empty/None."""
    assert _derive_identity_slug(None, "Alice Wonderland") == "alice-wonderland"
    assert _derive_identity_slug("", "Alice Wonderland") == "alice-wonderland"


def test_derive_identity_slug_both_empty_returns_none():
    """Should return None when both email and name are empty/None (derivation failure)."""
    assert _derive_identity_slug(None, None) is None
    assert _derive_identity_slug("", "") is None


# ---------------------------------------------------------------------------
# _resolve_roadmap_relpath: three-state resolution + owner-line gate
# ---------------------------------------------------------------------------


def _config_with_roadmap_path(roadmap_path):
    return OrchestratorConfig(
        max_iterations=3,
        usage_threshold_5h=90,
        usage_threshold_weekly=95,
        enable_phase_sessions=False,
        roadmap_path=roadmap_path,
    )


def _fake_git_config(email=None, name=None):
    """Build a subprocess.run stand-in answering `git config user.email`/`user.name`."""
    class _Result:
        def __init__(self, returncode, stdout):
            self.returncode = returncode
            self.stdout = stdout

    def _run(cmd, cwd=None, capture_output=None, text=None):
        key = cmd[-1]
        value = email if key == "user.email" else name if key == "user.name" else None
        if value is None:
            return _Result(1, "")
        return _Result(0, value)

    return _run


def test_resolve_roadmap_relpath_absent_returns_default(tmp_path):
    """Should return 'ROADMAP.md' when roadmap_path is absent (byte-stable default)."""
    config = _config_with_roadmap_path(None)
    assert _resolve_roadmap_relpath(config, tmp_path) == "ROADMAP.md"


def test_resolve_roadmap_relpath_my_present_matching_owner(tmp_path, monkeypatch):
    """Should return the named relpath when the file exists and its owner line matches."""
    roadmaps_dir = tmp_path / ".ai-factory" / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    (roadmaps_dir / "john-doe.md").write_text("> Owner: john.doe@example.com\n\n- [ ] Task\n")
    monkeypatch.setattr(main_module.subprocess, "run", _fake_git_config(email="john.doe@example.com"))

    config = _config_with_roadmap_path("my")
    assert _resolve_roadmap_relpath(config, tmp_path) == "roadmaps/john-doe.md"


def test_resolve_roadmap_relpath_my_name_derived_owner_matches(tmp_path, monkeypatch):
    """Should match the owner line against `name` when git email is unset (name-fallback derivation)."""
    roadmaps_dir = tmp_path / ".ai-factory" / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    (roadmaps_dir / "alice.md").write_text("> Owner: Alice\n\n- [ ] Task\n")
    monkeypatch.setattr(main_module.subprocess, "run", _fake_git_config(email=None, name="Alice"))

    config = _config_with_roadmap_path("my")
    assert _resolve_roadmap_relpath(config, tmp_path) == "roadmaps/alice.md"


def test_resolve_roadmap_relpath_my_missing_file_falls_back(tmp_path, monkeypatch):
    """Should fall back to 'ROADMAP.md' with a loud message when the named roadmap is missing."""
    monkeypatch.setattr(main_module.subprocess, "run", _fake_git_config(email="john.doe@example.com"))

    config = _config_with_roadmap_path("my")
    assert _resolve_roadmap_relpath(config, tmp_path) == "ROADMAP.md"


def test_resolve_roadmap_relpath_my_owner_mismatch_raises_halt(tmp_path, monkeypatch):
    """Should raise HaltError when the owner line names a different identity."""
    roadmaps_dir = tmp_path / ".ai-factory" / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    (roadmaps_dir / "john-doe.md").write_text("> Owner: someone.else@gmail.com\n\n- [ ] Task\n")
    monkeypatch.setattr(main_module.subprocess, "run", _fake_git_config(email="john.doe@example.com"))

    config = _config_with_roadmap_path("my")
    with pytest.raises(HaltError):
        _resolve_roadmap_relpath(config, tmp_path)


def test_resolve_roadmap_relpath_my_malformed_first_line_raises_halt(tmp_path, monkeypatch):
    """Should raise HaltError when the file's first line isn't a well-formed owner line."""
    roadmaps_dir = tmp_path / ".ai-factory" / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    (roadmaps_dir / "john-doe.md").write_text("# Not an owner line\n\n- [ ] Task\n")
    monkeypatch.setattr(main_module.subprocess, "run", _fake_git_config(email="john.doe@example.com"))

    config = _config_with_roadmap_path("my")
    with pytest.raises(HaltError):
        _resolve_roadmap_relpath(config, tmp_path)


def test_resolve_roadmap_relpath_my_derivation_failure_raises_halt(tmp_path, monkeypatch):
    """Should raise HaltError when neither git email nor name is set (derivation failure)."""
    monkeypatch.setattr(main_module.subprocess, "run", _fake_git_config(email=None, name=None))

    config = _config_with_roadmap_path("my")
    with pytest.raises(HaltError):
        _resolve_roadmap_relpath(config, tmp_path)


def test_resolve_roadmap_relpath_explicit_returned_verbatim(tmp_path):
    """Should return an explicit value verbatim, with no owner check."""
    config = _config_with_roadmap_path("roadmaps/alice.md")
    assert _resolve_roadmap_relpath(config, tmp_path) == "roadmaps/alice.md"


# ---------------------------------------------------------------------------
# _tests_sibling: derive the test-roadmap sibling from the roadmap in play
# ---------------------------------------------------------------------------


def test_tests_sibling_default_pair_is_special_cased():
    """Should map 'ROADMAP.md' to 'ROADMAP_TESTS.md' (not '-tests' suffixing)."""
    assert _tests_sibling("ROADMAP.md") == "ROADMAP_TESTS.md"


def test_tests_sibling_named_roadmap_uses_suffix():
    """Should map a named roadmap to its '-tests' suffixed sibling in the same directory."""
    assert _tests_sibling("roadmaps/john-doe.md") == "roadmaps/john-doe-tests.md"


# ---------------------------------------------------------------------------
# _artifact_subdir: key artifact dirs by the roadmap file's stem; default pair stays flat
# ---------------------------------------------------------------------------


def test_artifact_subdir_default_roadmap_is_flat():
    """Should return None for the default 'ROADMAP.md' (byte-stable flat layout)."""
    assert _artifact_subdir("ROADMAP.md") is None


def test_artifact_subdir_default_tests_roadmap_is_flat():
    """Should return None for the default 'ROADMAP_TESTS.md' (byte-stable flat layout)."""
    assert _artifact_subdir("ROADMAP_TESTS.md") is None


def test_artifact_subdir_named_roadmap_uses_stem():
    """Should key a named roadmap's artifacts by its stem."""
    assert _artifact_subdir("roadmaps/john-doe.md") == "john-doe"


def test_artifact_subdir_named_tests_roadmap_uses_stem():
    """Should key a named test-roadmap sibling by its main roadmap's stem (one stem per roadmap pair)."""
    assert _artifact_subdir("roadmaps/john-doe-tests.md") == "john-doe"


def test_artifact_subdir_explicit_path_tests_sibling_uses_stem():
    """Should key an explicit, non-'roadmaps/' roadmap's test sibling by its main roadmap's stem."""
    assert _artifact_subdir("custom-tests.md") == "custom"


def test_artifact_subdir_track_file_uses_stem():
    """Should key any other roadmap file (e.g. a track file) by its stem."""
    assert _artifact_subdir("ROADMAP.watch.md") == "ROADMAP.watch"


# ---------------------------------------------------------------------------
# _detect_milestone_step over subdir'd artifact dirs — dispatch unchanged one level deeper
# ---------------------------------------------------------------------------


def test_detect_milestone_step_subdird_dirs_dispatches_same_as_flat(tmp_path):
    """Should dispatch identically to the flat case when plans/plan-reviews/reviews are nested one level deeper under a per-roadmap subdir."""
    plans_dir = tmp_path / ".ai-factory" / "plans" / "john-doe"
    plan_reviews_dir = tmp_path / ".ai-factory" / "plan-reviews" / "john-doe"
    reviews_dir = tmp_path / ".ai-factory" / "reviews" / "john-doe"
    plans_dir.mkdir(parents=True)
    plan_reviews_dir.mkdir(parents=True)
    reviews_dir.mkdir(parents=True)
    plan_path = plans_dir / f"{DMS_SEQ}-{DMS_SLUG}.md"
    plan_path.write_text("# Plan content")
    plan_path.with_suffix(".json").write_text(json.dumps({"step": "implemented"}))
    step, counter, returned_path = _detect_milestone_step(
        tmp_path, DMS_SEQ, DMS_SLUG, plan_path, plan_reviews_dir, reviews_dir
    )
    assert step == "review"
    assert counter == 1
    assert returned_path == plan_path


# ---------------------------------------------------------------------------
# _next_number: max-based numbering over well-formed files
# ---------------------------------------------------------------------------


def test_next_number_empty_directory_returns_one(tmp_path):
    """Should return 1 when the directory is empty (the `if not existing: return 1` branch)."""
    assert _next_number(tmp_path) == 1


def test_next_number_single_well_formed_file_returns_one_past(tmp_path):
    """Should return one past the number when a single well-formed file exists."""
    (tmp_path / "03-x.md").write_text("")
    assert _next_number(tmp_path) == 4


def test_next_number_gap_returns_one_past_highest(tmp_path):
    """Should return one past the highest number, not the count, when files exist with a gap
    (pinning max+1 vs. a naive count+1 that would return 4)."""
    (tmp_path / "01-a.md").write_text("")
    (tmp_path / "02-b.md").write_text("")
    (tmp_path / "05-c.md").write_text("")
    assert _next_number(tmp_path) == 6


# ---------------------------------------------------------------------------
# _next_number: mixed digit / non-digit stems
# ---------------------------------------------------------------------------


def test_next_number_skips_later_sorting_non_digit_stem(tmp_path):
    """Should ignore a non-digit stem regardless of position and take the digit stem's value
    into the max: only "01-a.md" contributes a number, so the result is 1 + 1 == 2."""
    (tmp_path / "01-a.md").write_text("")
    (tmp_path / "zz-notes.md").write_text("")
    assert _next_number(tmp_path) == 2


def test_next_number_skips_earlier_sorting_non_digit_stem(tmp_path):
    """Should ignore a non-digit stem regardless of position and take the digit stem's value
    into the max: only "02-b.md" contributes a number, so the result is 2 + 1 == 3.
    Deliberate complement to the zz-notes case above — exercises the opposite placement of
    the stray non-digit file, confirming non-digit stems are excluded irrespective of order."""
    (tmp_path / "aa-notes.md").write_text("")
    (tmp_path / "02-b.md").write_text("")
    assert _next_number(tmp_path) == 3


def test_next_number_no_digit_stems_falls_back_to_count_plus_one(tmp_path):
    """Should fall back to count + 1 when no file has a digit-prefixed stem (the loop exhausts
    without returning, hitting the `len(existing)+1` fallback line)."""
    (tmp_path / "notes.md").write_text("")
    (tmp_path / "readme.md").write_text("")
    assert _next_number(tmp_path) == 3


# ---------------------------------------------------------------------------
# _next_number: double-digit rollover and the lexicographic-sort boundary
# ---------------------------------------------------------------------------


def test_next_number_rolls_from_single_to_double_digit(tmp_path):
    """Should roll from single- to double-digit numbering: the max over the parsed values
    [8, 9] yields 10, independent of any sort order or digit width."""
    (tmp_path / "08-a.md").write_text("")
    (tmp_path / "09-b.md").write_text("")
    assert _next_number(tmp_path) == 10


def test_next_number_sole_double_digit_entry(tmp_path):
    """Should return the correct next number when the sole entry is already a double-digit file
    (guards an off-by-one specific to multi-character digit prefixes)."""
    (tmp_path / "10-c.md").write_text("")
    assert _next_number(tmp_path) == 11


def test_next_number_mixed_width_resolves_numerically(tmp_path):
    """Should resolve a mixed-width set by numeric value, not string order: "9-a.md" and
    "10-b.md" yield max(9, 10) + 1 == 11, regardless of how the stems would sort as strings."""
    (tmp_path / "9-a.md").write_text("")
    (tmp_path / "10-b.md").write_text("")
    assert _next_number(tmp_path) == 11


def test_next_number_three_digit_width_boundary(tmp_path):
    """Should resolve past the two-to-three-digit width boundary numerically: "99-x.md" and
    "100-y.md" yield max(99, 100) + 1 == 101, not the already-used 100 that a lexicographic
    (string-sort) comparison would collide on."""
    (tmp_path / "99-x.md").write_text("")
    (tmp_path / "100-y.md").write_text("")
    assert _next_number(tmp_path) == 101
