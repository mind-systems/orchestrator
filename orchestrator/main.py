"""Orchestrator — Agent 1: loop through roadmap milestones."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .agents import Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, RateLimitError, RefactorPlanner
from .roadmap import mark_done, mark_skipped, parse_roadmap
from . import state


def _load_state(project_dir: Path) -> dict:
    state_path = project_dir / ".ai-factory" / "orchestrator-state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(project_dir: Path, data: dict) -> None:
    state_path = project_dir / ".ai-factory" / "orchestrator-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(data, indent=2))


def _handle_sigint(sig, frame):
    if state.stop_requested:
        print("\n>>> Force quit.")
        sys.exit(1)
    state.stop_requested = True
    print("\n>>> Will stop after the current milestone finishes. Press Ctrl+C again to force quit.")


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


def process_milestone(project_dir: Path, milestone, milestone_index: int, max_iterations: int = 3) -> None:
    """Plan → implement → review loop for a single milestone."""
    ai_factory = project_dir / ".ai-factory"
    plans_dir = ai_factory / "plans"
    patches_dir = ai_factory / "patches"
    reviews_dir = ai_factory / "reviews"
    plans_dir.mkdir(parents=True, exist_ok=True)
    patches_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)

    seq = f"{milestone_index:02d}"
    plan_path = plans_dir / f"{seq}-{milestone.slug}.md"
    print(f"\n{'='*60}")
    print(f"MILESTONE: {milestone.title}")
    print(f"{'='*60}")

    # Create agents
    planner_reviewer = PlannerReviewer(project_dir)
    implementer = Implementer(project_dir)
    milestone_start = time.monotonic()

    # Step 1: Plan
    print("\n>>> PLANNING...")
    planner_reviewer.plan(milestone.title, milestone.description, plan_path)

    if not plan_path.exists():
        print(f">>> Planner did not create a plan (milestone may already be done). Skipping.")
        roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"
        mark_skipped(roadmap_path, milestone)
        return

    # Step 1.5: Plan review (fresh context, one pass)
    print("\n>>> REVIEWING PLAN...")
    plan_reviewer = PlanReviewer(project_dir)
    plan_passed, plan_feedback = plan_reviewer.review_plan(plan_path)
    if not plan_passed:
        print(">>> Plan has issues — sending feedback to planner...")
        planner_reviewer.plan(
            milestone.title, milestone.description, plan_path,
            feedback=plan_feedback,
        )

    # Step 2-3: Implement → Review loop
    orch_state = _load_state(project_dir)
    implement_reviews: list[str] = orch_state.setdefault("implement_reviews", [])

    for iteration in range(1, max_iterations + 1):
        print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
        implementer.implement(plan_path, patches_dir)

        print(f"\n>>> REVIEWING (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        review_path = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration}.md"
        passed = planner_reviewer.review(plan_path, review_path)

        implement_reviews.append(review_path.name)
        _save_state(project_dir, orch_state)

        if passed:
            print(f">>> REVIEW PASSED — see {review_path}")
            break
        else:
            print(f">>> Review found issues — see {review_path}")
            if iteration == max_iterations:
                print(f"WARNING: Max iterations ({max_iterations}) reached. Moving on.")

    # Step 4: Mark done + commit
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"
    mark_done(roadmap_path, milestone)
    _git_commit(project_dir, milestone.title)

    elapsed = int(time.monotonic() - milestone_start)
    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")


def process_refactor_milestone(project_dir: Path, milestone, milestone_index: int, max_iterations: int = 3) -> None:
    """Audit → implement → verify loop for a single refactor milestone."""
    ai_factory = project_dir / ".ai-factory"
    plans_dir = ai_factory / "plans"
    patches_dir = ai_factory / "patches"
    reviews_dir = ai_factory / "reviews"
    plans_dir.mkdir(parents=True, exist_ok=True)
    patches_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)

    seq = f"{milestone_index:02d}"
    plan_path = plans_dir / f"{seq}-{milestone.slug}.md"
    print(f"\n{'='*60}")
    print(f"MILESTONE: {milestone.title}")
    print(f"{'='*60}")

    # Create agents
    refactor_planner = RefactorPlanner(project_dir)
    implementer = Implementer(project_dir)
    milestone_start = time.monotonic()

    # Step 1: Audit + plan
    print("\n>>> AUDITING...")
    refactor_planner.audit_and_plan(milestone.title, milestone.description, plan_path)

    # Step 2-3: Implement → Verify loop
    for iteration in range(1, max_iterations + 1):
        print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
        implementer.implement(plan_path, patches_dir)

        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        review_path = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration}.md"

        print(f"\n>>> VERIFYING (iteration {iteration})...")
        passed = refactor_planner.verify(plan_path, review_path)

        if passed:
            print(f">>> VERIFY PASSED — see {review_path}")
            break
        else:
            # Bridge verify findings to patches_dir so Implementer can read them
            patch_path = patches_dir / f"{seq}-{milestone.slug}-patch-{iteration}.md"
            patch_path.write_text(review_path.read_text())
            if iteration == max_iterations:
                raise PipelineStopError(
                    f"Max iterations ({max_iterations}) reached.\n\n"
                    f"Last review: {review_path}\n\n{review_path.read_text()}"
                )

    # Step 4: Mark done + commit
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"
    mark_done(roadmap_path, milestone)
    _git_commit(project_dir, milestone.title)

    elapsed = int(time.monotonic() - milestone_start)
    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")


def review_plan(project_dir: Path, plan_path: Path, max_iterations: int = 3) -> None:
    """Review → patch → implement → review loop for a single plan."""
    ai_factory = project_dir / ".ai-factory"
    patches_dir = ai_factory / "patches"
    reviews_dir = ai_factory / "reviews"
    patches_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)

    slug = plan_path.stem  # e.g. "01-project-scaffold"
    print(f"\n{'='*60}")
    print(f"REVIEWING PLAN: {plan_path.name}")
    print(f"{'='*60}")

    planner_reviewer = PlannerReviewer(project_dir)
    implementer = Implementer(project_dir)
    plan_start = time.monotonic()

    for iteration in range(1, max_iterations + 1):
        print(f"\n>>> REVIEWING (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        review_path = reviews_dir / f"{slug}-review-{iteration}.md"
        passed = planner_reviewer.review(plan_path, review_path)

        if passed:
            print(f">>> REVIEW PASSED — see {review_path}")
            break

        print(f">>> Review found issues — see {review_path}")

        if iteration == max_iterations:
            print(f"WARNING: Max iterations ({max_iterations}) reached. Moving on.")
            break

        # Planner creates a detailed patch from the review
        print(f"\n>>> PATCHING (iteration {iteration})...")
        patch_path = patches_dir / f"{slug}-patch-{iteration}.md"
        planner_reviewer.patch(review_path, patch_path)

        # Implementer applies the patch
        print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
        implementer.implement(plan_path, patches_dir)

    # Build commit message from the last review's critical findings
    review_files = sorted(reviews_dir.glob(f"{slug}-review-*.md"))
    last_review = review_files[-1] if review_files else None
    commit_msg = plan_path.stem.replace("-", " ", 1)  # "22 signal dispatch computation loop"
    if last_review:
        lines = last_review.read_text().splitlines()
        # Collect issue titles (### N. ...) — numbered headings are actual findings
        issues = []
        for l in lines:
            if l.startswith("### ") and l[4:5].isdigit():
                title = l.lstrip("# ").strip()
                # Remove leading "N. " numbering
                title = title.split(". ", 1)[-1] if ". " in title else title
                issues.append(title)
        if issues:
            commit_msg += "\n\n" + "\n".join(f"- {i}" for i in issues[:5])
    _git_commit(project_dir, commit_msg)

    elapsed = int(time.monotonic() - plan_start)
    mins, secs = divmod(elapsed, 60)
    print(f">>> Plan review done [{mins}m {secs}s]")


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


def _implement_loop(project_dir: Path, max_iterations: int = 3) -> None:
    """Plan + implement all pending milestones. No review."""
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"

    if not roadmap_path.exists():
        print(f"ERROR: No ROADMAP.md found at {roadmap_path}")
        sys.exit(1)

    milestones = parse_roadmap(roadmap_path)
    pending = [m for m in milestones if not m.done]

    if not pending:
        print("All milestones are done!")
        return

    print(f"Found {len(pending)} pending milestones out of {len(milestones)} total.")

    plans_dir = project_dir / ".ai-factory" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    for i, milestone in enumerate(pending, start=_next_number(plans_dir)):
        if state.stop_requested:
            print("\n>>> Stop requested — halting before next milestone.")
            return
        process_milestone(project_dir, milestone, i, max_iterations)


def _refactor_loop(project_dir: Path, max_iterations: int = 3) -> None:
    """Run refactor pipeline on all pending milestones."""
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"

    if not roadmap_path.exists():
        print(f"ERROR: No ROADMAP.md found at {roadmap_path}")
        sys.exit(1)

    milestones = parse_roadmap(roadmap_path)
    pending = [m for m in milestones if not m.done]

    if not pending:
        print("All milestones are done!")
        return

    print(f"Found {len(pending)} pending milestones out of {len(milestones)} total.")

    plans_dir = project_dir / ".ai-factory" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    for i, milestone in enumerate(pending, start=_next_number(plans_dir)):
        if state.stop_requested:
            print("\n>>> Stop requested — halting before next milestone.")
            return
        process_refactor_milestone(project_dir, milestone, i, max_iterations)


def run_implement(project_dir: Path, max_iterations: int = 3) -> None:
    """Implement only — plan + implement milestones, no review pass."""
    signal.signal(signal.SIGINT, _handle_sigint)
    time_str = _with_caffeinate(_implement_loop, project_dir, max_iterations)
    print(f"\n{'='*60}")
    print(f"IMPLEMENT DONE — {time_str}")
    print(f"{'='*60}")


def run_refactor(project_dir: Path, max_iterations: int = 3) -> None:
    """Run refactor pipeline on pending milestones."""
    signal.signal(signal.SIGINT, _handle_sigint)
    time_str = _with_caffeinate(_refactor_loop, project_dir, max_iterations)
    print(f"\n{'='*60}")
    print(f"REFACTOR DONE — {time_str}")
    print(f"{'='*60}")


def run_implement_review(project_dir: Path, max_iterations: int = 3) -> None:
    """Implement all milestones, then run review pass on all plans."""
    signal.signal(signal.SIGINT, _handle_sigint)

    def loop():
        _implement_loop(project_dir, max_iterations)

        # Delete only the review files created during this implement pass
        orch_state = _load_state(project_dir)
        implement_reviews: list[str] = orch_state.pop("implement_reviews", [])
        _save_state(project_dir, orch_state)

        if implement_reviews:
            reviews_dir = project_dir / ".ai-factory" / "reviews"
            deleted = 0
            for name in implement_reviews:
                f = reviews_dir / name
                if f.exists():
                    f.unlink()
                    deleted += 1
            print(f"\n>>> Cleared {deleted} implement-phase review(s). Starting review flow...")

        review_loop = run_review(project_dir, max_iterations)
        if review_loop:
            review_loop()

    time_str = _with_caffeinate(loop)
    print(f"\n{'='*60}")
    print(f"ALL DONE — {time_str}")
    print(f"{'='*60}")


def run_review(project_dir: Path, max_iterations: int = 3):
    """Review all existing plans against the current codebase. Returns the review loop callable, or None if nothing to review."""
    plans_dir = project_dir / ".ai-factory" / "plans"

    if not plans_dir.exists():
        print(f"ERROR: No plans directory found at {plans_dir}")
        sys.exit(1)

    plan_files = sorted(plans_dir.glob("*.md"))
    if not plan_files:
        print("No plan files found.")
        return

    reviews_dir = project_dir / ".ai-factory" / "reviews"

    def _already_passed(plan_path: Path) -> bool:
        slug = plan_path.stem
        for review_file in sorted(reviews_dir.glob(f"{slug}-review-*.md")):
            if review_file.read_text().strip().endswith("REVIEW_PASS"):
                return True
        return False

    pending = [p for p in plan_files if not _already_passed(p)]
    skipped = len(plan_files) - len(pending)
    if skipped:
        print(f"Skipping {skipped} already-passed plans.")
    if not pending:
        print("All plans already passed review.")
        return
    print(f"Found {len(pending)} plans to review.")

    def loop():
        for plan_path in pending:
            review_plan(project_dir, plan_path, max_iterations)

    return loop


def cli() -> None:
    parser = argparse.ArgumentParser(description="AI orchestrator — plan, implement, review from roadmap")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    for cmd, help_text in [
        ("implement", "Plan and implement milestones (no review pass)"),
        ("review", "Review all existing plans against current codebase"),
        ("implement-review", "Implement milestones, then run review pass on all plans"),
        ("refactor", "Run refactor pipeline on pending milestones"),
    ]:
        p = subparsers.add_parser(cmd, help=help_text)
        p.add_argument("project_dir", nargs="?", default=".", help="Path to the project directory")

    args = parser.parse_args()
    project_dir = Path(args.project_dir).resolve() if hasattr(args, "project_dir") and args.project_dir else Path(".").resolve()

    max_iterations = int(os.environ.get("ORCHESTRATOR_MAX_ITERATIONS", "3"))

    try:
        if args.command == "review":
            signal.signal(signal.SIGINT, _handle_sigint)
            loop = run_review(project_dir, max_iterations)
            if loop:
                time_str = _with_caffeinate(loop)
                print(f"\n{'='*60}")
                print(f"ALL PLANS REVIEWED — {time_str}")
                print(f"{'='*60}")
        elif args.command == "implement-review":
            run_implement_review(project_dir, max_iterations)
        elif args.command == "refactor":
            run_refactor(project_dir, max_iterations)
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
