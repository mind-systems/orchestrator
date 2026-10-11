"""The flow: the per-task pipeline, the mode record and its instances, and the roadmap loop."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import NamedTuple

from .agents import REVIEW_VERIFY, TEST_RUN_VERIFY, Implementer, PlannerReviewer, PlanReviewer
from .config import OrchestratorConfig
from .errors import EscalationError, HaltError, PipelineStopError
from .notify import Outcome, report
from .ports import VerifyKind
from .protocol import PLAN_REVIEW_PASS, _read_sessions, _write_session
from .resume import _detect_step
from .roadmap import mark_done, mark_skipped, parse_roadmap
from .runtime import _run_summary
from .usage import _check_usage_limits
from . import state


class Mode(NamedTuple):
    """Static per-mode divergences between the implement and test pipelines."""
    roadmap_relpath: str  # path relative to `.ai-factory/`
    header_label: str
    planner_prompt_name: str
    skip_message: str
    verify: VerifyKind
    artifact_subdir: str | None = None  # per-roadmap artifact dir segment; None = flat (default pair)


IMPLEMENT_MODE = Mode(
    roadmap_relpath="ROADMAP.md",
    header_label="TASK",
    planner_prompt_name="planner",
    skip_message="Planner did not create a plan (task may already be done). Skipping.",
    verify=REVIEW_VERIFY,
)

TEST_MODE = Mode(
    roadmap_relpath="ROADMAP_TESTS.md",
    header_label="TEST TASK",
    planner_prompt_name="test-planner",
    skip_message="Planner did not create a plan. Skipping.",
    verify=TEST_RUN_VERIFY,
)


def _next_number(directory: Path) -> int:
    """Return the next sequential number based on existing files in directory."""
    existing = list(directory.glob("*.md"))
    if not existing:
        return 1
    numbers = [
        int(parts[0])
        for f in existing
        if (parts := f.stem.split("-", 1))[0].isdigit()
    ]
    if numbers:
        return max(numbers) + 1
    return len(existing) + 1


def _artifact_dir(project_dir: Path, mode: Mode, dirname: str) -> Path:
    """The artifact directory `dirname`, under the mode's per-roadmap subdirectory when it has one; creates nothing."""
    base = project_dir / ".ai-factory" / dirname
    return base / mode.artifact_subdir if mode.artifact_subdir else base


def _git_commit(project_dir: Path, task_title: str) -> None:
    """Stage all changes and commit after a completed task."""
    subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
    # Check if there's anything to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=project_dir,
    )
    if result.returncode == 0:
        print(">>> Nothing to commit, skipping.")
        return
    message = f"{task_title}\n\nCo-Authored-By: AI Orchestrator <noreply@orchestrator>"
    subprocess.run(["git", "commit", "-m", message], cwd=project_dir, check=True)
    print(f">>> COMMITTED: {task_title}")

    push_result = subprocess.run(
        ["git", "push", "-u", "origin", "HEAD"], cwd=project_dir,
    )
    if push_result.returncode != 0:
        print(">>> WARNING: git push failed, continuing anyway.")


def process_task(project_dir: Path, task, task_index: int, config: OrchestratorConfig, mode: Mode = IMPLEMENT_MODE, phase_session_id: str | None = None) -> str | None:
    """Plan → implement → verify loop for a single task (verify = review, or a real test run in test mode)."""
    max_iterations = config.max_iterations
    plans_dir = _artifact_dir(project_dir, mode, "plans")
    output_dir = _artifact_dir(project_dir, mode, mode.verify.output_dirname)
    plan_reviews_dir = _artifact_dir(project_dir, mode, "plan-reviews")
    plans_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_reviews_dir.mkdir(parents=True, exist_ok=True)

    roadmap_path = project_dir / ".ai-factory" / mode.roadmap_relpath
    seq = f"{task_index:02d}"
    plan_path = plans_dir / f"{seq}-{task.slug}.md"
    print(f"\n{'='*60}")
    print(f"{mode.header_label}: {task.title}")
    print(f"{'='*60}")

    step, counter, plan_path = _detect_step(
        project_dir, seq, task.slug, plan_path, plan_reviews_dir, output_dir,
        mode.verify,
    )
    seq = plan_path.stem.split("-", 1)[0]

    elapsed_offset = 0
    sessions: dict[str, str] = {}
    if plan_path.exists():
        sessions = _read_sessions(plan_path)
        elapsed_offset = int(sessions.get("elapsed", "0"))
    task_start = time.monotonic() - elapsed_offset

    if step != "plan":
        print(f">>> Resuming from step '{step}' (counter={counter})")

    if step == "escalated":
        raise EscalationError(sessions.get("escalation", "(no escalation detail recorded)"))

    if step == "done":
        elapsed = int(time.monotonic() - task_start)
        mark_done(roadmap_path, task, elapsed)
        state.tasks_done += 1
        _git_commit(project_dir, task.title)
        report(config, Outcome.TASK_DONE, project_dir.name, task.title, _run_summary())
        mins, secs = divmod(elapsed, 60)
        print(f">>> Task done [{mins}m {secs}s]")
        return phase_session_id

    # Create agents
    planner_reviewer = PlannerReviewer(project_dir, planner_prompt_name=mode.planner_prompt_name)
    implementer = Implementer(project_dir)
    verifier = mode.verify.make_verifier(planner_reviewer, project_dir)

    if sessions and sessions.get("planner"):
        planner_reviewer.session_id = sessions.get("planner")
    elif phase_session_id:
        planner_reviewer.session_id = phase_session_id
    implementer.session_id = sessions.get("implementer") if sessions else None

    # Step 1: Plan
    if step == "plan":
        print("\n>>> PLANNING...")
        if counter > 1:
            prev_plan_review = plan_reviews_dir / f"{seq}-{task.slug}-plan-review-{counter - 1}.md"
            planner_reviewer.plan(task.title, task.description, plan_path, roadmap_path=roadmap_path, line_number=task.line_number, plan_review_path=prev_plan_review)
        else:
            planner_reviewer.plan(task.title, task.description, plan_path, roadmap_path=roadmap_path, line_number=task.line_number)

        if not plan_path.exists():
            print(f">>> {mode.skip_message}")
            mark_skipped(roadmap_path, task)
            return planner_reviewer.session_id

        step = "plan_review"
        _write_session(plan_path, "step", f"planned:{counter}")
        _write_session(plan_path, "elapsed", str(int(time.monotonic() - task_start)))

    # Step 1.5: Iterative plan review
    if step in ("plan", "plan_review"):
        for attempt in range(counter, max_iterations + 1):
            print(f"\n>>> REVIEWING PLAN (attempt {attempt})...")
            plan_reviewer = PlanReviewer(project_dir)
            plan_review_path = plan_reviews_dir / f"{seq}-{task.slug}-plan-review-{attempt}.md"
            plan_passed = plan_reviewer.review_plan(plan_path, plan_review_path, attempt)
            _write_session(plan_path, "elapsed", str(int(time.monotonic() - task_start)))

            if plan_passed:
                print(f">>> Plan review passed — see {plan_review_path}")
                _write_session(plan_path, "step", "plan_reviewed")
                break

            if attempt == max_iterations:
                raise PipelineStopError(
                    f"Plan failed\n\n"
                    f"Last review: {plan_review_path}\n\n{plan_review_path.read_text()}"
                )

            print(">>> Plan has issues — revising plan...")
            _write_session(plan_path, "step", f"plan_review_failed:{attempt}")
            planner_reviewer.plan(
                task.title, task.description, plan_path,
                plan_review_path=plan_review_path,
            )
            _write_session(plan_path, "step", f"planned:{attempt + 1}")

    # Safety guard: ensure a passing plan review exists before implementing
    _plan_review_files = sorted(plan_reviews_dir.glob(f"{seq}-{task.slug}-plan-review-*.md"))
    if not _plan_review_files or not _plan_review_files[-1].read_text().strip().endswith(PLAN_REVIEW_PASS):
        raise PipelineStopError(
            f"No passing plan review found for task {seq}-{task.slug}. Cannot proceed to implementation."
        )

    # Step 2-3: Implement → Verify loop
    impl_start = counter if step in ("implement", mode.verify.step) else 1
    if impl_start > max_iterations:
        raise HaltError(
            f"Resume at iteration {impl_start} exceeds max_iterations "
            f"({max_iterations}). Raise max_iterations in orchestrator.json to continue."
        )
    for iteration in range(impl_start, max_iterations + 1):
        if step == mode.verify.step and iteration == counter:
            # Resuming mid-verify: implementation already done, go straight to verify
            pass
        else:
            print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
            feedback_path = output_dir / f"{seq}-{task.slug}{mode.verify.output_suffix.format(n=iteration - 1)}" if iteration > 1 else None
            implementer.implement(plan_path, feedback_path=feedback_path, roadmap_path=roadmap_path, line_number=task.line_number)
            _write_session(plan_path, "step", f"implemented:{iteration}")
            _write_session(plan_path, "elapsed", str(int(time.monotonic() - task_start)))

        print(f"\n>>> {mode.verify.running_header} (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        out_path = output_dir / f"{seq}-{task.slug}{mode.verify.output_suffix.format(n=iteration)}"
        prev_out_path = None
        if iteration > 1:
            prev = output_dir / f"{seq}-{task.slug}{mode.verify.output_suffix.format(n=iteration - 1)}"
            if prev.exists():
                prev_out_path = prev
        passed = verifier.verify(plan_path, out_path, prev_out_path)
        _write_session(plan_path, "elapsed", str(int(time.monotonic() - task_start)))

        if passed:
            print(f">>> {mode.verify.pass_line_label} — see {out_path}")
            break
        else:
            print(f">>> {mode.verify.fail_line_label} — see {out_path}")
            _write_session(plan_path, "step", f"{mode.verify.fail_tag}{iteration}")
            if iteration == max_iterations:
                raise PipelineStopError(
                    mode.verify.max_iterations_message.format(n=max_iterations, path=out_path, content=out_path.read_text())
                )

    # Step 4: Mark done + commit
    elapsed = int(time.monotonic() - task_start)
    mark_done(roadmap_path, task, elapsed)
    state.tasks_done += 1
    _git_commit(project_dir, task.title)
    report(config, Outcome.TASK_DONE, project_dir.name, task.title, _run_summary())

    mins, secs = divmod(elapsed, 60)
    print(f">>> Task done [{mins}m {secs}s]")
    return planner_reviewer.session_id


def _run_dynamic_loop(project_dir: Path, roadmap_path: Path, config: OrchestratorConfig, process_fn, mode: Mode) -> None:
    """Dynamically re-scan the roadmap before each task, always running the first unchecked one."""
    plans_dir = _artifact_dir(project_dir, mode, "plans")
    plans_dir.mkdir(parents=True, exist_ok=True)
    phase_sessions_enabled = config.enable_phase_sessions

    # Startup summary (printed once)
    result = parse_roadmap(roadmap_path)
    pending = [m for m in result.tasks if not m.done]
    if not pending:
        print("All tasks are done!")
        return
    if result.breakpoint_hit:
        total = len(result.tasks) + result.tasks_after_breakpoint
        print(f"Found {len(pending)} pending tasks out of {total} total (stopped at breakpoint — {result.tasks_after_breakpoint} tasks after marker not queued).")
    else:
        print(f"Found {len(pending)} pending tasks out of {len(result.tasks)} total.")

    current_section: str | None = None
    phase_session_id: str | None = None
    last_signature: tuple[str, str] | None = None

    while not state.stop_requested:
        result = parse_roadmap(roadmap_path)
        pending = [m for m in result.tasks if not m.done]
        if not pending:
            report(config, Outcome.RUN_DONE, project_dir.name, None, _run_summary())
            break

        task = pending[0]
        signature = (task.title, task.description)
        if signature == last_signature:
            raise PipelineStopError(
                f"Task '{task.title}' checkbox is still unchecked after processing. "
                f"Refusing to re-run the same task forever — check mark_done / mark_skipped."
            )
        last_signature = signature

        i = _next_number(plans_dir)
        _check_usage_limits(config)

        if task.section != current_section:
            current_section = task.section
            phase_session_id = None
        elif not phase_sessions_enabled:
            phase_session_id = None

        phase_session_id = process_fn(task, i, phase_session_id)

    if state.stop_requested:
        print("\n>>> Stop requested — halting.")
        report(config, Outcome.MANUAL_STOP, project_dir.name, None, _run_summary())
