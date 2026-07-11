"""Orchestrator — Agent 1: loop through roadmap milestones."""

from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

from .agents import HaltError, Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, TestRunner, _read_sessions, _write_session
from .config import OrchestratorConfig, load_config
from .notify import notify
from .resume import _detect_step
from .roadmap import ParseResult, mark_done, mark_skipped, parse_roadmap
from .runtime import _handle_sigint, _run_elapsed, _with_caffeinate
from .usage import _check_usage_limits
from . import state


class Mode(NamedTuple):
    """Static per-mode divergences between the implement and test pipelines."""
    roadmap_relpath: str  # path relative to `.ai-factory/`
    header_label: str
    planner_prompt_name: str
    output_dirname: str
    output_suffix: str  # artifact tail with an {n} placeholder, e.g. "-review-{n}.md"
    verify_step: str
    verify_fail_tag: str
    pass_signal: str
    skip_message: str
    verify_running_header: str
    pass_line_label: str
    fail_line_label: str
    max_iterations_message: str  # template with {n}, {path}, {content} placeholders
    artifact_subdir: str | None = None  # per-roadmap artifact dir segment; None = flat (default pair)


IMPLEMENT_MODE = Mode(
    roadmap_relpath="ROADMAP.md",
    header_label="MILESTONE",
    planner_prompt_name="planner",
    output_dirname="reviews",
    output_suffix="-review-{n}.md",
    verify_step="review",
    verify_fail_tag="review_failed:",
    pass_signal="REVIEW_PASS",
    skip_message="Planner did not create a plan (milestone may already be done). Skipping.",
    verify_running_header="REVIEWING",
    pass_line_label="REVIEW PASSED",
    fail_line_label="Review found issues",
    max_iterations_message="Max iterations ({n}) reached without REVIEW_PASS.\n\nLast review: {path}\n\n{content}",
)

TEST_MODE = Mode(
    roadmap_relpath="ROADMAP_TESTS.md",
    header_label="TEST MILESTONE",
    planner_prompt_name="test-planner",
    output_dirname="test-runs",
    output_suffix="-test-{n}.txt",
    verify_step="test_run",
    verify_fail_tag="test_run_failed:",
    pass_signal="TEST_PASS",
    skip_message="Planner did not create a plan. Skipping.",
    verify_running_header="RUNNING TESTS",
    pass_line_label="TESTS PASSED",
    fail_line_label="Tests failed",
    max_iterations_message="Tests failed after {n} iteration(s).\n\nLast run: {path}\n\n{content}",
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


def _derive_identity_slug(email: str | None, name: str | None) -> str | None:
    """Slug from the email local-part, falling back to name; None if both are empty."""
    def _slugify(value: str) -> str | None:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or None

    if email:
        slug = _slugify(email.split("@", 1)[0])
        if slug:
            return slug
    if name:
        slug = _slugify(name)
        if slug:
            return slug
    return None


def _git_config_value(project_dir: Path, key: str) -> str | None:
    """Read a single git config value in project_dir; None on any failure or empty value."""
    result = subprocess.run(
        ["git", "config", key], cwd=project_dir, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _resolve_roadmap_relpath(config: OrchestratorConfig, project_dir: Path) -> str:
    """Three explicit states keyed on config.roadmap_path: absent, 'my', or an explicit path."""
    if config.roadmap_path is None:
        return "ROADMAP.md"

    if config.roadmap_path == "my":
        email = _git_config_value(project_dir, "user.email")
        name = _git_config_value(project_dir, "user.name")
        slug = _derive_identity_slug(email, name)
        if slug is None:
            raise HaltError(
                "roadmap_path is 'my' but no git identity is set — "
                "set git user.email or user.name, or use an explicit roadmap_path."
            )
        relpath = f"roadmaps/{slug}.md"
        roadmap_file = project_dir / ".ai-factory" / relpath
        if not roadmap_file.exists():
            print(f">>> Named roadmap {relpath} not found — falling back to ROADMAP.md")
            return "ROADMAP.md"

        lines = roadmap_file.read_text().splitlines()
        first_line = lines[0] if lines else ""
        identity = email or name
        expected_owner = f"> Owner: {identity}"
        if first_line.strip() != expected_owner:
            raise HaltError(
                f"Named roadmap {relpath} owner line ({first_line!r}) does not match "
                f"the current git identity ({expected_owner!r})."
            )
        return relpath

    return config.roadmap_path


def _tests_sibling(relpath: str) -> str:
    """Derive the test-roadmap sibling path from the roadmap in play."""
    if relpath == "ROADMAP.md":
        return "ROADMAP_TESTS.md"
    path = Path(relpath)
    return str(path.parent / f"{path.stem}-tests{path.suffix}")


def _artifact_subdir(relpath: str) -> str | None:
    """Key artifact dirs by the roadmap file's stem; the default pair stays flat (None)."""
    if relpath in ("ROADMAP.md", "ROADMAP_TESTS.md"):
        return None
    return Path(relpath).stem


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


def process_milestone(project_dir: Path, milestone, milestone_index: int, config: OrchestratorConfig, mode: Mode = IMPLEMENT_MODE, phase_session_id: str | None = None) -> str | None:
    """Plan → implement → verify loop for a single milestone (verify = review, or a real test run in test mode)."""
    max_iterations = config.max_iterations
    ai_factory = project_dir / ".ai-factory"
    plans_dir = ai_factory / "plans"
    output_dir = ai_factory / mode.output_dirname
    plan_reviews_dir = ai_factory / "plan-reviews"
    if mode.artifact_subdir:
        plans_dir = plans_dir / mode.artifact_subdir
        output_dir = output_dir / mode.artifact_subdir
        plan_reviews_dir = plan_reviews_dir / mode.artifact_subdir
    plans_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_reviews_dir.mkdir(parents=True, exist_ok=True)

    roadmap_path = project_dir / ".ai-factory" / mode.roadmap_relpath
    seq = f"{milestone_index:02d}"
    plan_path = plans_dir / f"{seq}-{milestone.slug}.md"
    print(f"\n{'='*60}")
    print(f"{mode.header_label}: {milestone.title}")
    print(f"{'='*60}")

    step, counter, plan_path = _detect_step(
        project_dir, seq, milestone.slug, plan_path, plan_reviews_dir, output_dir,
        mode.verify_step, mode.verify_fail_tag, mode.output_suffix, mode.pass_signal,
    )
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
    planner_reviewer = PlannerReviewer(project_dir, planner_prompt_name=mode.planner_prompt_name)
    implementer = Implementer(project_dir)
    test_runner = TestRunner() if mode.verify_step == "test_run" else None

    def _verify(out_path: Path, prev_out_path: Path | None) -> bool:
        if test_runner is not None:
            return test_runner.run(plan_path, out_path, project_dir)
        return planner_reviewer.review(plan_path, out_path, prev_review_path=prev_out_path)

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
            print(f">>> {mode.skip_message}")
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

    # Step 2-3: Implement → Verify loop
    impl_start = counter if step in ("implement", mode.verify_step) else 1
    if impl_start > max_iterations:
        raise HaltError(
            f"Resume at iteration {impl_start} exceeds max_iterations "
            f"({max_iterations}). Raise max_iterations in orchestrator.json to continue."
        )
    for iteration in range(impl_start, max_iterations + 1):
        if step == mode.verify_step and iteration == counter:
            # Resuming mid-verify: implementation already done, go straight to verify
            pass
        else:
            print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
            feedback_path = output_dir / f"{seq}-{milestone.slug}{mode.output_suffix.format(n=iteration - 1)}" if iteration > 1 else None
            implementer.implement(plan_path, feedback_path=feedback_path, roadmap_path=roadmap_path, line_number=milestone.line_number)
            _write_session(plan_path, "step", "implemented")
            _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

        print(f"\n>>> {mode.verify_running_header} (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        out_path = output_dir / f"{seq}-{milestone.slug}{mode.output_suffix.format(n=iteration)}"
        prev_out_path = None
        if mode.verify_step == "review" and iteration > 1:
            prev = output_dir / f"{seq}-{milestone.slug}{mode.output_suffix.format(n=iteration - 1)}"
            if prev.exists():
                prev_out_path = prev
        passed = _verify(out_path, prev_out_path)
        _write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))

        if passed:
            print(f">>> {mode.pass_line_label} — see {out_path}")
            break
        else:
            print(f">>> {mode.fail_line_label} — see {out_path}")
            _write_session(plan_path, "step", f"{mode.verify_fail_tag}{iteration}")
            if iteration == max_iterations:
                raise PipelineStopError(
                    mode.max_iterations_message.format(n=max_iterations, path=out_path, content=out_path.read_text())
                )

    # Step 4: Mark done + commit
    elapsed = int(time.monotonic() - milestone_start)
    mark_done(roadmap_path, milestone, elapsed)
    _git_commit(project_dir, milestone.title)
    notify(config, f"{project_dir.name}: Milestone done: {milestone.title}", "milestone")

    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")
    return planner_reviewer.session_id


def _run_dynamic_loop(project_dir: Path, roadmap_path: Path, config: OrchestratorConfig, process_fn, artifact_subdir: str | None = None) -> None:
    """Dynamically re-scan the roadmap before each milestone, always running the first unchecked one."""
    plans_dir = project_dir / ".ai-factory" / "plans"
    if artifact_subdir:
        plans_dir = plans_dir / artifact_subdir
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
            notify(config, f"All milestones done: {project_dir.name}\nRan for {_run_elapsed()}", "done")
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
        notify(config, f"Orchestrator stopped (manual): {project_dir.name}\nRan for {_run_elapsed()}", "stop")


def _test_loop(project_dir: Path, config: OrchestratorConfig) -> None:
    """Write tests for all pending milestones from the roadmap's test sibling."""
    main_relpath = _resolve_roadmap_relpath(config, project_dir)
    relpath = _tests_sibling(main_relpath)
    roadmap_path = project_dir / ".ai-factory" / relpath
    if not roadmap_path.exists():
        print(f"ERROR: No roadmap found at {roadmap_path}")
        sys.exit(1)
    mode = TEST_MODE._replace(roadmap_relpath=relpath, artifact_subdir=_artifact_subdir(relpath))
    _run_dynamic_loop(
        project_dir, roadmap_path, config,
        lambda m, i, sid: process_milestone(project_dir, m, i, config, mode, phase_session_id=sid),
        artifact_subdir=mode.artifact_subdir,
    )


def _implement_loop(project_dir: Path, config: OrchestratorConfig, planner_prompt_name: str = "planner", roadmap_relpath: str | None = None) -> None:
    """Plan + implement all pending milestones. No review."""
    relpath = roadmap_relpath or _resolve_roadmap_relpath(config, project_dir)
    roadmap_path = project_dir / ".ai-factory" / relpath
    if not roadmap_path.exists():
        print(f"ERROR: No roadmap found at {roadmap_path}")
        sys.exit(1)
    mode = IMPLEMENT_MODE._replace(planner_prompt_name=planner_prompt_name, roadmap_relpath=relpath, artifact_subdir=_artifact_subdir(relpath))
    _run_dynamic_loop(
        project_dir, roadmap_path, config,
        lambda m, i, sid: process_milestone(project_dir, m, i, config, mode, phase_session_id=sid),
        artifact_subdir=mode.artifact_subdir,
    )


def run_implement(project_dir: Path, config: OrchestratorConfig) -> None:
    """Implement only — plan + implement milestones, no review pass."""
    state.config = config
    state.project_dir = project_dir
    state.run_started = time.monotonic()
    signal.signal(signal.SIGINT, _handle_sigint)
    time_str = _with_caffeinate(_implement_loop, project_dir, config)
    print(f"\n{'='*60}")
    print(f"IMPLEMENT DONE — {time_str}")
    print(f"{'='*60}")


def run_test(project_dir: Path, config: OrchestratorConfig) -> None:
    """Test mode — plan + implement tests, gate on real test runner output."""
    state.config = config
    state.project_dir = project_dir
    state.run_started = time.monotonic()
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
        notify(config, f"Orchestrator stopped: {project_dir.name}\n{msg}\nRan for {_run_elapsed()}", "milestone-fail")
        sys.exit(0)
    except HaltError as e:
        print(f"\n{'='*60}")
        print(f"HALTED — {e}")
        print(f"{'='*60}")
        msg = str(e).splitlines()[0]
        notify(config, f"Orchestrator halted: {project_dir.name}\n{msg}\nRan for {_run_elapsed()}", "stop")
        sys.exit(0)
    except Exception as e:
        notify(
            config,
            f"Orchestrator error: {project_dir.name}\n{type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}\nRan for {_run_elapsed()}",
            "stop",
        )
        raise


if __name__ == "__main__":
    cli()
