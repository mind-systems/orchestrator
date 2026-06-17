"""Orchestrator — Agent 1: loop through roadmap milestones."""

from __future__ import annotations

import argparse
import math
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from .agents import Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, RateLimitError, TestRunner, _read_sessions, _write_session
from .roadmap import ParseResult, mark_done, mark_skipped, parse_roadmap
from . import state



def _handle_sigint(sig, frame):
    if state.stop_requested:
        print("\n>>> Force quit.")
        sys.exit(1)
    state.stop_requested = True
    print("\n>>> Will stop after the current milestone finishes. Press Ctrl+C again to force quit.")


def _parse_usage_pct() -> float | None:
    """Run `claude /usage` and extract the current session usage percentage."""
    try:
        result = subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30)
        m = re.search(r"Current session:\s+(\d+(?:\.\d+)?)%\s+used", result.stdout)
        return float(m.group(1)) if m else None
    except Exception:
        return None


class UsageGuard:
    """Polls `claude /usage` adaptively and stops the pipeline before hitting the session limit."""

    def __init__(self, threshold: float = 90.0):
        self.threshold = threshold
        self._history: list[tuple[int, float]] = []
        self._next_check_at: int = 0

    def check(self, idx: int) -> None:
        if idx < self._next_check_at:
            return
        pct = _parse_usage_pct()
        if pct is None:
            print("  [usage check: could not parse output, continuing]")
            self._next_check_at = idx + 5
            return
        print(f"  [usage: session {pct:.0f}% used]")
        if pct >= self.threshold:
            raise PipelineStopError(
                f"Session usage at {pct:.0f}% — stopping (threshold: {self.threshold:.0f}%)."
            )
        self._history.append((idx, pct))
        self._next_check_at = self._predict_next(idx, pct)

    def _predict_next(self, idx: int, pct: float) -> int:
        if len(self._history) < 2:
            return idx + 1
        oldest_idx, oldest_pct = self._history[0]
        span = idx - oldest_idx
        if span == 0:
            return idx + 5
        avg_delta = (pct - oldest_pct) / span
        if avg_delta <= 0:
            return idx + 5
        milestones_left = math.ceil((self.threshold - pct) / avg_delta)
        return idx + max(1, milestones_left - 1)


def _run_loop(items, process_fn, before_each=None) -> None:
    """Iterate over items, checking stop_requested before each."""
    for i, item in enumerate(items):
        if state.stop_requested:
            print("\n>>> Stop requested — halting.")
            return
        if before_each is not None:
            before_each(i, item)
        process_fn(item)


def _next_number(directory: Path) -> int:
    """Return the next sequential number based on existing files in directory."""
    existing = sorted(directory.glob("*.md"))
    if not existing:
        return 1
    for f in reversed(existing):
        parts = f.stem.split("-", 1)
        if parts[0].isdigit():
            return int(parts[0]) + 1
    return len(existing) + 1


def _git_commit(project_dir: Path, milestone_title: str) -> None:
    """Stage all changes and commit after a completed milestone."""
    subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
    # Check if there's anything to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=project_dir,
    )
    if result.returncode == 0:
        print(">>> Nothing to commit, skipping.")
        return
    message = f"{milestone_title}\n\nCo-Authored-By: AI Orchestrator <noreply@orchestrator>"
    subprocess.run(["git", "commit", "-m", message], cwd=project_dir, check=True)
    print(f">>> COMMITTED: {milestone_title}")


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


def _detect_milestone_step(
    project_dir: Path, seq: str, slug: str,
    plan_path: Path, plan_reviews_dir: Path, reviews_dir: Path,
) -> tuple[str, int, Path]:
    """Detect where a previous run stopped and return (step, counter, plan_path) to resume from.

    Steps: "plan", "plan_review", "implement", "review", "done".
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
        sessions.get("step", ""), seq, slug, plan_reviews_dir, reviews_dir,
        "review_failed:", "-review-{n}.md",
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
            return ("review", 1, plan_path)
        elif step_value.startswith("review_failed:"):
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

    # 6. No review files → need to do first review
    review_files = sorted(reviews_dir.glob(f"{seq}-{slug}-review-*.md"))
    if not review_files:
        return ("review", 1, plan_path)

    # 7. Latest review didn't pass → need to re-implement
    if not review_files[-1].read_text().strip().endswith("REVIEW_PASS"):
        return ("implement", len(review_files) + 1, plan_path)

    # 8. All steps complete
    return ("done", 0, plan_path)


def process_milestone(project_dir: Path, milestone, milestone_index: int, max_iterations: int = 3, planner_prompt_name: str = "planner", roadmap_filename: str = "ROADMAP.md", phase_session_id: str | None = None) -> str | None:
    """Plan → implement → review loop for a single milestone."""
    ai_factory = project_dir / ".ai-factory"
    plans_dir = ai_factory / "plans"
    patches_dir = ai_factory / "patches"
    reviews_dir = ai_factory / "reviews"
    plan_reviews_dir = ai_factory / "plan-reviews"
    plans_dir.mkdir(parents=True, exist_ok=True)
    patches_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    plan_reviews_dir.mkdir(parents=True, exist_ok=True)

    roadmap_path = project_dir / ".ai-factory" / roadmap_filename
    seq = f"{milestone_index:02d}"
    plan_path = plans_dir / f"{seq}-{milestone.slug}.md"
    print(f"\n{'='*60}")
    print(f"MILESTONE: {milestone.title}")
    print(f"{'='*60}")

    step, counter, plan_path = _detect_milestone_step(project_dir, seq, milestone.slug, plan_path, plan_reviews_dir, reviews_dir)
    seq = plan_path.stem.split("-", 1)[0]

    elapsed_offset = 0
    sessions: dict[str, str] = {}
    if plan_path.exists():
        sessions = _read_sessions(plan_path)
        elapsed_offset = int(sessions.get("elapsed", "0"))
    milestone_start = time.monotonic() - elapsed_offset

    if step != "plan":
        print(f">>> Resuming from step '{step}' (counter={counter})")

    if step == "done":
        elapsed = int(time.monotonic() - milestone_start)
        mark_done(roadmap_path, milestone, elapsed)
        _git_commit(project_dir, milestone.title)
        mins, secs = divmod(elapsed, 60)
        print(f">>> Milestone done [{mins}m {secs}s]")
        return phase_session_id

    # Create agents
    planner_reviewer = PlannerReviewer(project_dir, planner_prompt_name=planner_prompt_name)
    implementer = Implementer(project_dir)

    if sessions and sessions.get("planner"):
        planner_reviewer.session_id = sessions.get("planner")
    elif phase_session_id:
        planner_reviewer.session_id = phase_session_id
    implementer.session_id = sessions.get("implementer") if sessions else None

    # Step 1: Plan
    if step == "plan":
        print("\n>>> PLANNING...")
        if counter > 1:
            prev_plan_review = plan_reviews_dir / f"{seq}-{milestone.slug}-plan-review-{counter - 1}.md"
            planner_reviewer.plan(milestone.title, milestone.description, plan_path, roadmap_path=roadmap_path, line_number=milestone.line_number, plan_review_path=prev_plan_review)
        else:
            planner_reviewer.plan(milestone.title, milestone.description, plan_path, roadmap_path=roadmap_path, line_number=milestone.line_number)

        if not plan_path.exists():
            print(f">>> Planner did not create a plan (milestone may already be done). Skipping.")
            mark_skipped(roadmap_path, milestone)
            return planner_reviewer.session_id

        step = "plan_review"
        _write_session(plan_path, "step", "planned")
        _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

    # Step 1.5: Iterative plan review
    if step in ("plan", "plan_review"):
        for attempt in range(counter, max_iterations + 1):
            print(f"\n>>> REVIEWING PLAN (attempt {attempt})...")
            plan_reviewer = PlanReviewer(project_dir)
            plan_review_path = plan_reviews_dir / f"{seq}-{milestone.slug}-plan-review-{attempt}.md"
            plan_passed = plan_reviewer.review_plan(plan_path, plan_review_path)
            _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

            if plan_passed:
                print(f">>> Plan review passed — see {plan_review_path}")
                _write_session(plan_path, "step", "plan_reviewed")
                break

            if attempt == max_iterations:
                raise PipelineStopError(
                    f"Plan failed review after {max_iterations} attempt(s).\n\n"
                    f"Last review: {plan_review_path}\n\n{plan_review_path.read_text()}"
                )

            print(">>> Plan has issues — revising plan...")
            _write_session(plan_path, "step", f"plan_review_failed:{attempt}")
            planner_reviewer.plan(
                milestone.title, milestone.description, plan_path,
                plan_review_path=plan_review_path,
            )

    # Safety guard: ensure a passing plan review exists before implementing
    _plan_review_files = sorted(plan_reviews_dir.glob(f"{seq}-{milestone.slug}-plan-review-*.md"))
    if not _plan_review_files or not _plan_review_files[-1].read_text().strip().endswith("PLAN_REVIEW_PASS"):
        raise PipelineStopError(
            f"No passing plan review found for milestone {seq}-{milestone.slug}. Cannot proceed to implementation."
        )

    # Step 2-3: Implement → Review loop
    impl_start = counter if step in ("implement", "review") else 1
    if impl_start > max_iterations:
        raise PipelineStopError(
            f"Resume at iteration {impl_start} exceeds max_iterations "
            f"({max_iterations}). Bump ORCHESTRATOR_MAX_ITERATIONS to continue."
        )
    for iteration in range(impl_start, max_iterations + 1):
        if step == "review" and iteration == counter:
            # Resuming mid-review: implementation already done, go straight to review
            pass
        else:
            print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
            implementer.implement(plan_path, patches_dir, roadmap_path=roadmap_path, line_number=milestone.line_number)
            _write_session(plan_path, "step", "implemented")
            _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

        print(f"\n>>> REVIEWING (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        review_path = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration}.md"
        passed = planner_reviewer.review(plan_path, review_path)
        _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

        if passed:
            print(f">>> REVIEW PASSED — see {review_path}")
            break
        else:
            print(f">>> Review found issues — see {review_path}")
            _write_session(plan_path, "step", f"review_failed:{iteration}")
            if iteration == max_iterations:
                raise PipelineStopError(
                    f"Max iterations ({max_iterations}) reached without REVIEW_PASS.\n\n"
                    f"Last review: {review_path}\n\n{review_path.read_text()}"
                )

    # Step 4: Mark done + commit
    elapsed = int(time.monotonic() - milestone_start)
    mark_done(roadmap_path, milestone, elapsed)
    _git_commit(project_dir, milestone.title)

    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")
    return planner_reviewer.session_id


def _with_caffeinate(func, *args, **kwargs):
    """Run a function with macOS sleep prevention."""
    caffeinate = subprocess.Popen(["caffeinate", "-ims"])
    start = time.monotonic()
    try:
        func(*args, **kwargs)
    except Exception:
        elapsed = int(time.monotonic() - start)
        mins, secs = divmod(elapsed, 60)
        hours, mins = divmod(mins, 60)
        elapsed_str = f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"
        print(f">>> Ran for {elapsed_str} before stopping.")
        raise
    finally:
        caffeinate.send_signal(signal.SIGTERM)
        caffeinate.wait()

    elapsed = int(time.monotonic() - start)
    mins, secs = divmod(elapsed, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"


def _detect_test_milestone_step(
    project_dir: Path, seq: str, slug: str,
    plan_path: Path, plan_reviews_dir: Path, test_runs_dir: Path,
) -> tuple[str, int, Path]:
    """Detect where a previous test run stopped. Steps: plan, plan_review, implement, test_run, done."""
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

    if not plan_path.exists():
        return ("plan", 1, plan_path)

    # Check explicit step tracking from JSON sidecar
    sessions = _read_sessions(plan_path)
    step_value = _validate_sidecar_step(
        sessions.get("step", ""), seq, slug, plan_reviews_dir, test_runs_dir,
        "test_run_failed:", "-test-{n}.txt",
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
            return ("test_run", 1, plan_path)
        elif step_value.startswith("test_run_failed:"):
            n = int(step_value.split(":")[1])
            return ("implement", n + 1, plan_path)
        # unrecognized → fall through to heuristic

    plan_review_files = sorted(plan_reviews_dir.glob(f"{seq}-{slug}-plan-review-*.md"))
    if not plan_review_files:
        return ("plan_review", 1, plan_path)

    if not plan_review_files[-1].read_text().strip().endswith("PLAN_REVIEW_PASS"):
        return ("plan", len(plan_review_files) + 1, plan_path)

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

    test_run_files = sorted(test_runs_dir.glob(f"{seq}-{slug}-test-*.txt"))
    if not test_run_files:
        return ("test_run", 1, plan_path)

    if test_run_files[-1].read_text().strip().endswith("TEST_PASS"):
        return ("done", 0, plan_path)

    return ("implement", len(test_run_files) + 1, plan_path)


def process_test_milestone(project_dir: Path, milestone, milestone_index: int, max_iterations: int = 3, phase_session_id: str | None = None) -> str | None:
    """Plan → implement → test-run loop for a single test milestone."""
    ai_factory = project_dir / ".ai-factory"
    plans_dir = ai_factory / "plans"
    patches_dir = ai_factory / "patches"
    test_runs_dir = ai_factory / "test-runs"
    plan_reviews_dir = ai_factory / "plan-reviews"
    for d in (plans_dir, patches_dir, test_runs_dir, plan_reviews_dir):
        d.mkdir(parents=True, exist_ok=True)

    roadmap_path = project_dir / ".ai-factory" / "ROADMAP_TESTS.md"
    seq = f"{milestone_index:02d}"
    plan_path = plans_dir / f"{seq}-{milestone.slug}.md"
    print(f"\n{'='*60}")
    print(f"TEST MILESTONE: {milestone.title}")
    print(f"{'='*60}")

    step, counter, plan_path = _detect_test_milestone_step(project_dir, seq, milestone.slug, plan_path, plan_reviews_dir, test_runs_dir)
    seq = plan_path.stem.split("-", 1)[0]

    elapsed_offset = 0
    sessions: dict[str, str] = {}
    if plan_path.exists():
        sessions = _read_sessions(plan_path)
        elapsed_offset = int(sessions.get("elapsed", "0"))
    milestone_start = time.monotonic() - elapsed_offset

    if step != "plan":
        print(f">>> Resuming from step '{step}' (counter={counter})")

    if step == "done":
        elapsed = int(time.monotonic() - milestone_start)
        mark_done(roadmap_path, milestone, elapsed)
        _git_commit(project_dir, milestone.title)
        mins, secs = divmod(elapsed, 60)
        print(f">>> Milestone done [{mins}m {secs}s]")
        return phase_session_id

    planner_reviewer = PlannerReviewer(project_dir, planner_prompt_name="test-planner")
    implementer = Implementer(project_dir)
    test_runner = TestRunner()

    if sessions and sessions.get("planner"):
        planner_reviewer.session_id = sessions.get("planner")
    elif phase_session_id:
        planner_reviewer.session_id = phase_session_id
    implementer.session_id = sessions.get("implementer") if sessions else None

    # Step 1: Plan
    if step == "plan":
        print("\n>>> PLANNING...")
        if counter > 1:
            prev_plan_review = plan_reviews_dir / f"{seq}-{milestone.slug}-plan-review-{counter - 1}.md"
            planner_reviewer.plan(milestone.title, milestone.description, plan_path, roadmap_path=roadmap_path, line_number=milestone.line_number, plan_review_path=prev_plan_review)
        else:
            planner_reviewer.plan(milestone.title, milestone.description, plan_path, roadmap_path=roadmap_path, line_number=milestone.line_number)

        if not plan_path.exists():
            print(">>> Planner did not create a plan. Skipping.")
            mark_skipped(roadmap_path, milestone)
            return planner_reviewer.session_id

        step = "plan_review"
        _write_session(plan_path, "step", "planned")
        _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

    # Step 1.5: Iterative plan review
    if step in ("plan", "plan_review"):
        for attempt in range(counter, max_iterations + 1):
            print(f"\n>>> REVIEWING PLAN (attempt {attempt})...")
            plan_reviewer = PlanReviewer(project_dir)
            plan_review_path = plan_reviews_dir / f"{seq}-{milestone.slug}-plan-review-{attempt}.md"
            plan_passed = plan_reviewer.review_plan(plan_path, plan_review_path)
            _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

            if plan_passed:
                print(f">>> Plan review passed — see {plan_review_path}")
                _write_session(plan_path, "step", "plan_reviewed")
                break

            if attempt == max_iterations:
                raise PipelineStopError(
                    f"Plan failed review after {max_iterations} attempt(s).\n\n"
                    f"Last review: {plan_review_path}\n\n{plan_review_path.read_text()}"
                )

            print(">>> Plan has issues — revising plan...")
            _write_session(plan_path, "step", f"plan_review_failed:{attempt}")
            planner_reviewer.plan(
                milestone.title, milestone.description, plan_path,
                plan_review_path=plan_review_path,
            )

    _plan_review_files = sorted(plan_reviews_dir.glob(f"{seq}-{milestone.slug}-plan-review-*.md"))
    if not _plan_review_files or not _plan_review_files[-1].read_text().strip().endswith("PLAN_REVIEW_PASS"):
        raise PipelineStopError(
            f"No passing plan review found for milestone {seq}-{milestone.slug}. Cannot proceed to implementation."
        )

    # Step 2-3: Implement → TestRun loop
    impl_start = counter if step in ("implement", "test_run") else 1
    if impl_start > max_iterations:
        raise PipelineStopError(
            f"Resume at iteration {impl_start} exceeds max_iterations "
            f"({max_iterations}). Bump ORCHESTRATOR_MAX_ITERATIONS to continue."
        )
    for iteration in range(impl_start, max_iterations + 1):
        if step == "test_run" and iteration == counter:
            pass
        else:
            print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
            implementer.implement(plan_path, patches_dir, roadmap_path=roadmap_path, line_number=milestone.line_number)
            _write_session(plan_path, "step", "implemented")
            _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

        print(f"\n>>> RUNNING TESTS (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        test_run_path = test_runs_dir / f"{seq}-{milestone.slug}-test-{iteration}.txt"
        passed = test_runner.run(plan_path, test_run_path, project_dir)
        _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

        if passed:
            print(f">>> TESTS PASSED — see {test_run_path}")
            break
        else:
            print(f">>> Tests failed — see {test_run_path}")
            # Bridge test output to patches_dir so Implementer reads it on next iteration
            patch_path = patches_dir / f"{seq}-{milestone.slug}-patch-{iteration}.md"
            patch_path.write_text(test_run_path.read_text())
            _write_session(plan_path, "step", f"test_run_failed:{iteration}")
            if iteration == max_iterations:
                raise PipelineStopError(
                    f"Tests failed after {max_iterations} iteration(s).\n\n"
                    f"Last run: {test_run_path}\n\n{test_run_path.read_text()}"
                )

    # Step 4: Mark done + commit
    elapsed = int(time.monotonic() - milestone_start)
    mark_done(roadmap_path, milestone, elapsed)
    _git_commit(project_dir, milestone.title)

    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")
    return planner_reviewer.session_id


def _test_loop(project_dir: Path, max_iterations: int = 3) -> None:
    """Write tests for all pending milestones from ROADMAP_TESTS.md."""
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP_TESTS.md"

    if not roadmap_path.exists():
        print(f"ERROR: No ROADMAP_TESTS.md found at {roadmap_path}")
        sys.exit(1)

    result = parse_roadmap(roadmap_path)
    milestones = result.milestones
    pending = [m for m in milestones if not m.done]

    if not pending:
        print("All test milestones are done!")
        return

    if result.breakpoint_hit:
        total = len(milestones) + result.milestones_after_breakpoint
        print(f"Found {len(pending)} pending test milestones out of {total} total (stopped at breakpoint — {result.milestones_after_breakpoint} milestones after marker not queued).")
    else:
        print(f"Found {len(pending)} pending test milestones out of {len(milestones)} total.")

    plans_dir = project_dir / ".ai-factory" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    threshold = float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", "90"))
    guard = UsageGuard(threshold=threshold)

    current_section: str | None = None
    phase_session_id: str | None = None
    for i, milestone in enumerate(pending, start=_next_number(plans_dir)):
        if state.stop_requested:
            print("\n>>> Stop requested — halting.")
            break
        guard.check(i)
        if milestone.section != current_section:
            current_section = milestone.section
            phase_session_id = None
        phase_session_id = process_test_milestone(project_dir, milestone, i, max_iterations, phase_session_id=phase_session_id)


def _implement_loop(project_dir: Path, max_iterations: int = 3, planner_prompt_name: str = "planner", roadmap_filename: str = "ROADMAP.md") -> None:
    """Plan + implement all pending milestones. No review."""
    roadmap_path = project_dir / ".ai-factory" / roadmap_filename

    if not roadmap_path.exists():
        print(f"ERROR: No ROADMAP.md found at {roadmap_path}")
        sys.exit(1)

    result = parse_roadmap(roadmap_path)
    milestones = result.milestones
    pending = [m for m in milestones if not m.done]

    if not pending:
        print("All milestones are done!")
        return

    if result.breakpoint_hit:
        total = len(milestones) + result.milestones_after_breakpoint
        print(f"Found {len(pending)} pending milestones out of {total} total (stopped at breakpoint — {result.milestones_after_breakpoint} milestones after marker not queued).")
    else:
        print(f"Found {len(pending)} pending milestones out of {len(milestones)} total.")

    plans_dir = project_dir / ".ai-factory" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    threshold = float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", "90"))
    guard = UsageGuard(threshold=threshold)

    current_section: str | None = None
    phase_session_id: str | None = None
    for i, milestone in enumerate(pending, start=_next_number(plans_dir)):
        if state.stop_requested:
            print("\n>>> Stop requested — halting.")
            break
        guard.check(i)
        if milestone.section != current_section:
            current_section = milestone.section
            phase_session_id = None
        phase_session_id = process_milestone(project_dir, milestone, i, max_iterations, planner_prompt_name, roadmap_filename, phase_session_id=phase_session_id)


def run_implement(project_dir: Path, max_iterations: int = 3) -> None:
    """Implement only — plan + implement milestones, no review pass."""
    signal.signal(signal.SIGINT, _handle_sigint)
    time_str = _with_caffeinate(_implement_loop, project_dir, max_iterations)
    print(f"\n{'='*60}")
    print(f"IMPLEMENT DONE — {time_str}")
    print(f"{'='*60}")


def run_test(project_dir: Path, max_iterations: int = 3) -> None:
    """Test mode — plan + implement tests, gate on real test runner output."""
    signal.signal(signal.SIGINT, _handle_sigint)
    time_str = _with_caffeinate(_test_loop, project_dir, max_iterations)
    print(f"\n{'='*60}")
    print(f"TEST DONE — {time_str}")
    print(f"{'='*60}")


def cli() -> None:
    parser = argparse.ArgumentParser(description="AI orchestrator — plan, implement, review from roadmap")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    for cmd, help_text in [
        ("implement", "Plan and implement milestones"),
        ("test", "Write tests for milestones (uses test-planner prompt)"),
    ]:
        p = subparsers.add_parser(cmd, help=help_text)
        p.add_argument("project_dir", nargs="?", default=".", help="Path to the project directory")

    args = parser.parse_args()
    project_dir = Path(args.project_dir).resolve() if hasattr(args, "project_dir") and args.project_dir else Path(".").resolve()

    max_iterations = int(os.environ.get("ORCHESTRATOR_MAX_ITERATIONS", "3"))

    try:
        if args.command == "test":
            run_test(project_dir, max_iterations)
        else:
            run_implement(project_dir, max_iterations)
    except PipelineStopError as e:
        print(f"\n{'='*60}")
        print(f"STOPPED — {e}")
        print(f"{'='*60}")
        sys.exit(0)
    except RateLimitError as e:
        print(f"\n{'='*60}")
        print(f"STOPPED — Claude rate limit reached: {e}")
        print(f"{'='*60}")
        sys.exit(0)


if __name__ == "__main__":
    cli()
