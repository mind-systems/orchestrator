"""Orchestrator — Agent 1: loop through roadmap milestones."""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path

from .agents import Implementer, PlannerReviewer
from .roadmap import mark_done, parse_roadmap

MAX_REVIEW_ITERATIONS = 3


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
    message = f"{milestone_title}\n\nCo-Authored-By: AI Orchestrator <noreply@orchestrator>"
    subprocess.run(["git", "commit", "-m", message], cwd=project_dir, check=True)
    print(f">>> COMMITTED: {milestone_title}")


def process_milestone(project_dir: Path, milestone, milestone_index: int) -> None:
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
        print(f"ERROR: Plan file not created at {plan_path}")
        sys.exit(1)

    # Step 2-3: Implement → Review loop
    for iteration in range(1, MAX_REVIEW_ITERATIONS + 1):
        print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
        implementer.implement(plan_path, patches_dir)

        print(f"\n>>> REVIEWING (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        review_path = reviews_dir / f"{seq}-{milestone.slug}-review-{iteration}.md"
        passed = planner_reviewer.review(plan_path, review_path)

        if passed:
            print(f">>> REVIEW PASSED — see {review_path}")
            break
        else:
            print(f">>> Review found issues — see {review_path}")
            if iteration == MAX_REVIEW_ITERATIONS:
                print(f"WARNING: Max review iterations ({MAX_REVIEW_ITERATIONS}) reached. Moving on.")

    # Step 4: Mark done + commit
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"
    mark_done(roadmap_path, milestone)
    _git_commit(project_dir, milestone.title)

    elapsed = int(time.monotonic() - milestone_start)
    mins, secs = divmod(elapsed, 60)
    print(f">>> Milestone done [{mins}m {secs}s]")


def review_plan(project_dir: Path, plan_path: Path) -> None:
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

    for iteration in range(1, MAX_REVIEW_ITERATIONS + 1):
        print(f"\n>>> REVIEWING (iteration {iteration})...")
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        review_path = reviews_dir / f"{slug}-review-{iteration}.md"
        passed = planner_reviewer.review(plan_path, review_path)

        if passed:
            print(f">>> REVIEW PASSED — see {review_path}")
            break

        print(f">>> Review found issues — see {review_path}")

        if iteration == MAX_REVIEW_ITERATIONS:
            print(f"WARNING: Max review iterations ({MAX_REVIEW_ITERATIONS}) reached. Moving on.")
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
        # Collect issue titles (lines starting with ### under Critical Issues)
        issues = [l.lstrip("# ").strip() for l in lines if l.startswith("### ")]
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
    finally:
        caffeinate.send_signal(signal.SIGTERM)
        caffeinate.wait()

    elapsed = int(time.monotonic() - start)
    mins, secs = divmod(elapsed, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"


def run_implement(project_dir: Path) -> None:
    """Main orchestrator loop — plan, implement, review from roadmap."""
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

    def loop():
        for i, milestone in enumerate(pending, start=_next_number(plans_dir)):
            process_milestone(project_dir, milestone, i)

    time_str = _with_caffeinate(loop)

    print(f"\n{'='*60}")
    print(f"ALL MILESTONES COMPLETE — {time_str}")
    print(f"{'='*60}")


def run_review(project_dir: Path) -> None:
    """Review all existing plans against the current codebase."""
    plans_dir = project_dir / ".ai-factory" / "plans"

    if not plans_dir.exists():
        print(f"ERROR: No plans directory found at {plans_dir}")
        sys.exit(1)

    plan_files = sorted(plans_dir.glob("*.md"))
    if not plan_files:
        print("No plan files found.")
        return

    print(f"Found {len(plan_files)} plans to review.")

    def loop():
        for plan_path in plan_files:
            review_plan(project_dir, plan_path)

    time_str = _with_caffeinate(loop)

    print(f"\n{'='*60}")
    print(f"ALL PLANS REVIEWED — {time_str}")
    print(f"{'='*60}")


def cli() -> None:
    parser = argparse.ArgumentParser(description="AI orchestrator — plan, implement, review from roadmap")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Default: implement
    impl_parser = subparsers.add_parser("implement", help="Plan, implement, and review milestones from roadmap")
    impl_parser.add_argument("project_dir", nargs="?", default=".", help="Path to the project directory")

    # Review mode
    rev_parser = subparsers.add_parser("review", help="Review all existing plans against current codebase")
    rev_parser.add_argument("project_dir", nargs="?", default=".", help="Path to the project directory")

    args = parser.parse_args()
    project_dir = Path(args.project_dir).resolve() if hasattr(args, "project_dir") and args.project_dir else Path(".").resolve()

    if args.command == "review":
        run_review(project_dir)
    else:
        run_implement(project_dir)


if __name__ == "__main__":
    cli()
