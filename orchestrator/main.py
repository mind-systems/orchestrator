"""Orchestrator — Agent 1: loop through roadmap milestones."""

from __future__ import annotations

import argparse
import subprocess
import sys
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
    message = f"feat: {milestone_title}\n\nCo-Authored-By: AI Orchestrator <noreply@orchestrator>"
    subprocess.run(["git", "commit", "-m", message], cwd=project_dir, check=True)
    print(f">>> COMMITTED: {milestone_title}")


def process_milestone(project_dir: Path, milestone, milestone_index: int) -> None:
    """Plan → implement → review loop for a single milestone."""
    ai_factory = project_dir / ".ai-factory"
    plans_dir = ai_factory / "plans"
    patches_dir = ai_factory / "patches"
    plans_dir.mkdir(parents=True, exist_ok=True)
    patches_dir.mkdir(parents=True, exist_ok=True)

    seq = f"{milestone_index:02d}"
    plan_path = plans_dir / f"{seq}-{milestone.slug}.md"
    print(f"\n{'='*60}")
    print(f"MILESTONE: {milestone.title}")
    print(f"{'='*60}")

    # Create agents — each lives for the entire milestone
    planner = PlannerReviewer(project_dir)
    implementer = Implementer(project_dir)

    # Step 1: Plan
    print("\n>>> PLANNING...")
    planner.plan(milestone.title, milestone.description, plan_path)

    if not plan_path.exists():
        print(f"ERROR: Plan file not created at {plan_path}")
        sys.exit(1)

    # Step 2-3: Implement → Review loop
    for iteration in range(1, MAX_REVIEW_ITERATIONS + 1):
        print(f"\n>>> IMPLEMENTING (iteration {iteration})...")
        implementer.implement(plan_path, patches_dir)

        print(f"\n>>> REVIEWING (iteration {iteration})...")
        patch_path = patches_dir / f"{seq}-{milestone.slug}-review-{iteration}.md"
        passed = planner.review(plan_path, patch_path)

        if passed:
            print(">>> REVIEW PASSED")
            break
        else:
            print(f">>> Review found issues — see {patch_path}")
            if iteration == MAX_REVIEW_ITERATIONS:
                print(f"WARNING: Max review iterations ({MAX_REVIEW_ITERATIONS}) reached. Moving on.")

    # Step 4: Mark done + commit
    roadmap_path = project_dir / ".ai-factory" / "ROADMAP.md"
    mark_done(roadmap_path, milestone)
    _git_commit(project_dir, milestone.title)


def run(project_dir: Path) -> None:
    """Main orchestrator loop."""
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
        process_milestone(project_dir, milestone, i)

    print(f"\n{'='*60}")
    print("ALL MILESTONES COMPLETE")
    print(f"{'='*60}")


def cli() -> None:
    parser = argparse.ArgumentParser(description="AI orchestrator — plan, implement, review from roadmap")
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Path to the project directory (default: current directory)",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    run(project_dir)


if __name__ == "__main__":
    cli()
