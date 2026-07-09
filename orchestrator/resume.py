"""Resume / step-detection — figure out where a previous run stopped."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .agents import _read_sessions


def _validate_sidecar_step(
    step_value: str,
    seq: str,
    slug: str,
    plan_reviews_dir: Path,
    artifact_dir: Path,
    fail_prefix: str,
    fail_suffix: str,
) -> str:
    """Return step_value if the referenced artifact exists on disk, or "" if stale.

    Clears step_value when:
    - plan_review_failed:N and the corresponding plan-review file is missing.
    - plan_reviewed and no plan-review file ends with PLAN_REVIEW_PASS.
    - <fail_prefix>N and the corresponding artifact (artifact_dir / seq-slug<fail_suffix>) is missing.
    "planned" and "implemented" have no artifact reference and are always valid.
    Malformed :N parses also clear step_value so execution falls through to the heuristic.
    """
    if not step_value:
        return step_value
    if step_value in ("planned", "implemented"):
        return step_value
    if step_value.startswith("plan_review_failed:"):
        try:
            n = int(step_value.split(":")[1])
            if not (plan_reviews_dir / f"{seq}-{slug}-plan-review-{n}.md").exists():
                return ""
        except (IndexError, ValueError):
            return ""
        return step_value
    if step_value == "plan_reviewed":
        if not any(
            f.read_text().strip().endswith("PLAN_REVIEW_PASS")
            for f in plan_reviews_dir.glob(f"{seq}-{slug}-plan-review-*.md")
        ):
            return ""
        return step_value
    if step_value.startswith(fail_prefix):
        try:
            n = int(step_value.split(":")[1])
            if not (artifact_dir / f"{seq}-{slug}{fail_suffix.format(n=n)}").exists():
                return ""
        except (IndexError, ValueError):
            return ""
        return step_value
    # unrecognized → return as-is; dispatch will fall through to heuristic
    return step_value


def _detect_step(
    project_dir: Path, seq: str, slug: str,
    plan_path: Path, plan_reviews_dir: Path, output_dir: Path,
    verify_step: str, verify_fail_tag: str, output_suffix: str, pass_signal: str,
) -> tuple[str, int, Path]:
    """Detect where a previous run stopped and return (step, counter, plan_path) to resume from.

    Steps: "plan", "plan_review", "implement", <verify_step>, "done".
    Counter is the attempt/iteration number to use next.
    The returned plan_path is the canonical path discovered from the lowest-seq file matching
    the slug (handles the case where a previous run was interrupted and the current run computes
    a different seq via _next_number).
    """
    # Resolve canonical seq and plan_path by scanning for existing files with this slug.
    # This handles interrupted runs where _next_number() would otherwise produce a different seq.
    plans_dir = plan_path.parent
    slug_matches = sorted(plans_dir.glob(f"*-{slug}.md"))
    if slug_matches:
        best: Path | None = None
        best_num: int | None = None
        for f in slug_matches:
            parts = f.stem.split("-", 1)
            if parts[0].isdigit():
                num = int(parts[0])
                if best_num is None or num < best_num:
                    best_num = num
                    best = f
        if best is not None:
            seq = f"{best_num:02d}"
            plan_path = best

    # 1. Plan doesn't exist → start fresh
    if not plan_path.exists():
        return ("plan", 1, plan_path)

    # 2. Check explicit step tracking from JSON sidecar
    sessions = _read_sessions(plan_path)
    step_value = _validate_sidecar_step(
        sessions.get("step", ""), seq, slug, plan_reviews_dir, output_dir,
        verify_fail_tag, output_suffix,
    )
    if step_value:
        if step_value == "planned":
            return ("plan_review", 1, plan_path)
        elif step_value.startswith("plan_review_failed:"):
            n = int(step_value.split(":")[1])
            return ("plan", n + 1, plan_path)
        elif step_value == "plan_reviewed":
            return ("implement", 1, plan_path)
        elif step_value == "implemented":
            return (verify_step, 1, plan_path)
        elif step_value.startswith(verify_fail_tag):
            n = int(step_value.split(":")[1])
            return ("implement", n + 1, plan_path)
        # unrecognized → fall through to heuristic

    # 3. No plan-review files → need to do first plan review
    plan_review_files = sorted(plan_reviews_dir.glob(f"{seq}-{slug}-plan-review-*.md"))
    if not plan_review_files:
        return ("plan_review", 1, plan_path)

    # 4. Latest plan-review didn't pass → plan needs revision
    if not plan_review_files[-1].read_text().strip().endswith("PLAN_REVIEW_PASS"):
        return ("plan", len(plan_review_files) + 1, plan_path)

    # 5. Working tree is clean (excluding .ai-factory/ artifacts) → need to implement
    diff = subprocess.run(
        ["git", "diff", "HEAD", "--", ".", ":!.ai-factory"],
        cwd=project_dir, capture_output=True, text=True,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", ".", ":!.ai-factory"],
        cwd=project_dir, capture_output=True, text=True,
    )
    if not diff.stdout.strip() and not status.stdout.strip():
        return ("implement", 1, plan_path)

    # 6. No verify-output files → need to do first verify pass
    output_files = sorted(output_dir.glob(f"{seq}-{slug}{output_suffix.format(n='*')}"))
    if not output_files:
        return (verify_step, 1, plan_path)

    # 7. Latest verify-output passed → all steps complete; else need to re-implement
    if output_files[-1].read_text().strip().endswith(pass_signal):
        return ("done", 0, plan_path)

    return ("implement", len(output_files) + 1, plan_path)


def _detect_milestone_step(
    project_dir: Path, seq: str, slug: str,
    plan_path: Path, plan_reviews_dir: Path, reviews_dir: Path,
) -> tuple[str, int, Path]:
    """Detect where a previous implement run stopped. Thin wrapper over `_detect_step`.

    Literals below mirror `main.IMPLEMENT_MODE`'s verify_step/verify_fail_tag/output_suffix/pass_signal.
    """
    return _detect_step(
        project_dir, seq, slug, plan_path, plan_reviews_dir, reviews_dir,
        verify_step="review", verify_fail_tag="review_failed:",
        output_suffix="-review-{n}.md", pass_signal="REVIEW_PASS",
    )


def _detect_test_milestone_step(
    project_dir: Path, seq: str, slug: str,
    plan_path: Path, plan_reviews_dir: Path, test_runs_dir: Path,
) -> tuple[str, int, Path]:
    """Detect where a previous test run stopped. Thin wrapper over `_detect_step`.

    Literals below mirror `main.TEST_MODE`'s verify_step/verify_fail_tag/output_suffix/pass_signal.
    """
    return _detect_step(
        project_dir, seq, slug, plan_path, plan_reviews_dir, test_runs_dir,
        verify_step="test_run", verify_fail_tag="test_run_failed:",
        output_suffix="-test-{n}.txt", pass_signal="TEST_PASS",
    )
