"""Orchestrator — Agent 1: loop through roadmap milestones."""

from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from .agents import Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, RateLimitError, TestRunner, _read_sessions, _write_session, kill_active_child
from .config import OrchestratorConfig, load_config
from .notify import notify
from .roadmap import ParseResult, mark_done, mark_skipped, parse_roadmap
from . import state



def _handle_sigint(sig, frame):
    if state.stop_requested:
        print("\n>>> Force quit.")
        kill_active_child()
        sys.exit(1)
    state.stop_requested = True
    print("\n>>> Will stop after the current milestone finishes. Press Ctrl+C again to force quit.")


def _parse_pct(text: str, pattern: str) -> float | None:
    """Return the first captured group of pattern as float, or None if no match."""
    m = re.search(pattern, text)
    return float(m.group(1)) if m else None


def _check_usage_limits(config: OrchestratorConfig) -> None:
    """Run `claude /usage`, log current usage, and stop if either threshold is breached."""
    try:
        result = subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30)
        output = result.stdout
    except Exception:
        print("  [usage check: could not parse output, continuing]")
        return

    session_pct = _parse_pct(output, r"Current session:\s+(\d+(?:\.\d+)?)%")
    weekly_pct = _parse_pct(output, r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%")

    parts = []
    if session_pct is not None:
        parts.append(f"session {session_pct:.0f}%")
    if weekly_pct is not None:
        parts.append(f"week {weekly_pct:.0f}%")
    if parts:
        print(f"  [usage: {' · '.join(parts)}]")
    else:
        print("  [usage check: could not parse output, continuing]")
        return

    session_threshold = config.usage_threshold_5h
    weekly_threshold = config.usage_threshold_weekly

    if session_pct is not None and session_pct >= session_threshold:
        raise PipelineStopError(
            f"Session usage at {session_pct:.0f}% — stopping (threshold: {session_threshold:.0f}%)."
        )
    if weekly_pct is not None and weekly_pct >= weekly_threshold:
        raise PipelineStopError(
            f"Weekly usage at {weekly_pct:.0f}% — stopping (threshold: {weekly_threshold:.0f}%)."
        )


def _run_loop(items, process_fn) -> None:
    """Iterate over items, checking stop_requested before each."""
    for i, item in enumerate(items):
        if state.stop_requested:
            print("\n>>> Stop requested — halting.")
            return
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

    push_result = subprocess.run(
        ["git", "push", "-u", "origin", "HEAD"], cwd=project_dir,
    )
    if push_result.returncode != 0:
        print(">>> WARNING: git push failed, continuing anyway.")


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


def process_milestone(project_dir: Path, milestone, milestone_index: int, config: OrchestratorConfig, planner_prompt_name: str = "planner", roadmap_filename: str = "ROADMAP.md", phase_session_id: str | None = None) -> str | None:
    """Plan → implement → review loop for a single milestone."""
    max_iterations = config.max_iterations
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
        notify(config, f"{project_dir.name}: Milestone done: {milestone.title}", "milestone")
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
            f"({max_iterations}). Raise max_iterations in ~/.orchestrator.json to continue."
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
        prev_review_path = None
        if iteration > 1:
            prev = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration - 1}.md"
            if prev.exists():
                prev_review_path = prev
        passed = planner_reviewer.review(plan_path, review_path, prev_review_path=prev_review_path)
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
    notify(config, f"{project_dir.name}: Milestone done: {milestone.title}", "milestone")

    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")
    return planner_reviewer.session_id


def _fmt_elapsed(seconds: int) -> str:
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"


def _with_caffeinate(func, *args, **kwargs):
    """Run a function with macOS sleep prevention (degrades gracefully on non-macOS)."""
    start = time.monotonic()
    try:
        caffeinate = subprocess.Popen(["caffeinate", "-ims"])
    except FileNotFoundError:
        # caffeinate not available (non-macOS); run without sleep prevention
        try:
            func(*args, **kwargs)
        except Exception:
            elapsed = int(time.monotonic() - start)
            print(f">>> Ran for {_fmt_elapsed(elapsed)} before stopping.")
            raise
        return _fmt_elapsed(int(time.monotonic() - start))

    try:
        func(*args, **kwargs)
    except Exception:
        elapsed = int(time.monotonic() - start)
        print(f">>> Ran for {_fmt_elapsed(elapsed)} before stopping.")
        raise
    finally:
        caffeinate.send_signal(signal.SIGTERM)
        caffeinate.wait()

    return _fmt_elapsed(int(time.monotonic() - start))


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


def process_test_milestone(project_dir: Path, milestone, milestone_index: int, config: OrchestratorConfig, phase_session_id: str | None = None) -> str | None:
    """Plan → implement → test-run loop for a single test milestone."""
    max_iterations = config.max_iterations
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
        notify(config, f"{project_dir.name}: Milestone done: {milestone.title}", "milestone")
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
            f"({max_iterations}). Raise max_iterations in ~/.orchestrator.json to continue."
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
    notify(config, f"{project_dir.name}: Milestone done: {milestone.title}", "milestone")

    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")
    return planner_reviewer.session_id


def _run_dynamic_loop(project_dir: Path, roadmap_path: Path, config: OrchestratorConfig, process_fn) -> None:
    """Dynamically re-scan the roadmap before each milestone, always running the first unchecked one."""
    plans_dir = project_dir / ".ai-factory" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    phase_sessions_enabled = config.enable_phase_sessions

    # Startup summary (printed once)
    result = parse_roadmap(roadmap_path)
    pending = [m for m in result.milestones if not m.done]
    if not pending:
        print("All milestones are done!")
        return
    if result.breakpoint_hit:
        total = len(result.milestones) + result.milestones_after_breakpoint
        print(f"Found {len(pending)} pending milestones out of {total} total (stopped at breakpoint — {result.milestones_after_breakpoint} milestones after marker not queued).")
    else:
        print(f"Found {len(pending)} pending milestones out of {len(result.milestones)} total.")

    current_section: str | None = None
    phase_session_id: str | None = None
    last_signature: tuple[str, str] | None = None

    while not state.stop_requested:
        result = parse_roadmap(roadmap_path)
        pending = [m for m in result.milestones if not m.done]
        if not pending:
            notify(config, f"All milestones done: {project_dir.name}", "done")
            break

        milestone = pending[0]
        signature = (milestone.title, milestone.description)
        if signature == last_signature:
            raise PipelineStopError(
                f"Milestone '{milestone.title}' checkbox is still unchecked after processing. "
                f"Refusing to re-run the same milestone forever — check mark_done / mark_skipped."
            )
        last_signature = signature

        i = _next_number(plans_dir)
        _check_usage_limits(config)

        if milestone.section != current_section:
            current_section = milestone.section
            phase_session_id = None
        elif not phase_sessions_enabled:
            phase_session_id = None

        phase_session_id = process_fn(milestone, i, phase_session_id)

    if state.stop_requested:
        print("\n>>> Stop requested — halting.")


def _test_loop(project_dir: Path, config: OrchestratorConfig) -> None:
    """Write tests for all pending milestones from ROADMAP_TESTS.md."""
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP_TESTS.md"
    if not roadmap_path.exists():
        print(f"ERROR: No ROADMAP_TESTS.md found at {roadmap_path}")
        sys.exit(1)
    _run_dynamic_loop(
        project_dir, roadmap_path, config,
        lambda m, i, sid: process_test_milestone(project_dir, m, i, config, phase_session_id=sid),
    )


def _implement_loop(project_dir: Path, config: OrchestratorConfig, planner_prompt_name: str = "planner", roadmap_filename: str = "ROADMAP.md") -> None:
    """Plan + implement all pending milestones. No review."""
    roadmap_path = project_dir / ".ai-factory" / roadmap_filename
    if not roadmap_path.exists():
        print(f"ERROR: No ROADMAP.md found at {roadmap_path}")
        sys.exit(1)
    _run_dynamic_loop(
        project_dir, roadmap_path, config,
        lambda m, i, sid: process_milestone(project_dir, m, i, config, planner_prompt_name, roadmap_filename, phase_session_id=sid),
    )


def run_implement(project_dir: Path, config: OrchestratorConfig) -> None:
    """Implement only — plan + implement milestones, no review pass."""
    signal.signal(signal.SIGINT, _handle_sigint)
    time_str = _with_caffeinate(_implement_loop, project_dir, config)
    print(f"\n{'='*60}")
    print(f"IMPLEMENT DONE — {time_str}")
    print(f"{'='*60}")


def run_test(project_dir: Path, config: OrchestratorConfig) -> None:
    """Test mode — plan + implement tests, gate on real test runner output."""
    signal.signal(signal.SIGINT, _handle_sigint)
    time_str = _with_caffeinate(_test_loop, project_dir, config)
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

    config = load_config()

    try:
        if args.command == "test":
            run_test(project_dir, config)
        else:
            run_implement(project_dir, config)
    except PipelineStopError as e:
        print(f"\n{'='*60}")
        print(f"STOPPED — {e}")
        print(f"{'='*60}")
        msg = str(e).splitlines()[0]
        notify(config, f"Orchestrator stopped: {project_dir.name}\n{msg}", "stop")
        sys.exit(0)
    except RateLimitError as e:
        print(f"\n{'='*60}")
        print(f"STOPPED — Claude rate limit reached: {e}")
        print(f"{'='*60}")
        msg = str(e).splitlines()[0]
        notify(config, f"Orchestrator rate-limited: {project_dir.name}\n{msg}", "stop")
        sys.exit(0)


if __name__ == "__main__":
    cli()
