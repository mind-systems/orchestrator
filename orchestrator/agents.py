"""Agent runners — planner/reviewer and implementer via Claude Code CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _run_claude(
    prompt: str,
    cwd: str,
    system_prompt: str | None = None,
    allowed_tools: list[str] | None = None,
    session_id: str | None = None,
    model: str | None = None,
    effort: str | None = None,
) -> tuple[str, str]:
    """Run claude CLI and return (output_text, session_id)."""
    if allowed_tools is None:
        allowed_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]

    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--allowedTools", ",".join(allowed_tools),
    ]

    if model:
        cmd.extend(["--model", model])
    if effort:
        cmd.extend(["--effort", effort])

    if session_id:
        cmd.extend(["--resume", session_id])
    elif system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    print(f"\n--- Claude agent ({cwd}) ---")
    start = time.monotonic()
    proc = subprocess.Popen(
        cmd, cwd=cwd,
        stdout=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
    )

    try:
        stdout, _ = proc.communicate()
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
        print("\n>>> Interrupted by user")
        sys.exit(130)

    elapsed = int(time.monotonic() - start)
    mins, secs = divmod(elapsed, 60)

    if proc.returncode != 0:
        raise RuntimeError(f"Claude CLI failed with exit code {proc.returncode}")

    parsed = json.loads(stdout)
    output_text = parsed.get("result", "")
    sid = parsed.get("session_id", "")

    summary = output_text[:500] + ("..." if len(output_text) > 500 else "")
    print(f"{summary}\n  [{mins}m {secs}s]")

    return output_text, sid


class Planner:
    """Plans a milestone. Stateless — fresh session each call."""

    def __init__(
        self,
        project_dir: Path,
        model: str = "opus",
        effort: str = "high",
    ):
        self.project_dir = project_dir
        self.system_prompt = _load_prompt("planner")
        self.tools = ["Read", "Write", "Glob", "Grep", "Bash"]
        self.model = model
        self.effort = effort

    def plan(self, milestone_title: str, milestone_description: str, plan_path: Path) -> None:
        prompt = (
            f"Create an implementation plan for this milestone:\n\n"
            f"**{milestone_title}**\n"
            f"{milestone_description}\n\n"
            f"Write the plan to: {plan_path}\n"
        )

        _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )

    def patch(self, review_path: Path, patch_path: Path) -> None:
        """Read a review and create a detailed patch for the implementer."""
        prompt = (
            f"Read the review at: {review_path}\n"
            f"Create a detailed implementation patch that describes exactly what needs to be fixed.\n"
            f"For each issue, specify the file, the problem, and the exact fix.\n"
            f"Write the patch to: {patch_path}\n"
        )

        _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )


class Reviewer:
    """Reviews implementation against the plan. Fresh session — no shared context with planner."""

    def __init__(
        self,
        project_dir: Path,
        model: str = "opus",
        effort: str = "medium",
    ):
        self.project_dir = project_dir
        self.system_prompt = _load_prompt("reviewer")
        self.tools = ["Read", "Write", "Glob", "Grep", "Bash"]
        self.model = model
        self.effort = effort

    def review(self, plan_path: Path, review_path: Path) -> bool:
        """Review implementation against the plan. Always writes findings to review_path."""
        prompt = (
            f"The plan for context is at: {plan_path}\n"
            f"Review the CODE CHANGES for bugs, security issues, and correctness problems.\n"
            f"Run `git diff HEAD` and `git status` to see ALL changes.\n"
            f"Read each changed/new file IN FULL — understand the surrounding code, not just the diff.\n"
            f"Think about what will break at runtime: missing migrations, type mismatches, race conditions, etc.\n"
            f"Write your full review to: {review_path}\n"
            f"If no critical issues found, end the review file with REVIEW_PASS on its own line.\n"
        )

        output, _ = _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )

        return "REVIEW_PASS" in output


class Implementer:
    """Agent 3 — implements the plan, then applies fixes from patches. Same session."""

    def __init__(
        self,
        project_dir: Path,
        model: str = "sonnet",
        effort: str = "high",
    ):
        self.project_dir = project_dir
        self.system_prompt = _load_prompt("implementer")
        self.session_id: str | None = None
        self.tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
        self.model = model
        self.effort = effort

    def implement(self, plan_path: Path, patches_dir: Path) -> None:
        patches_note = ""
        if patches_dir.exists():
            patch_files = sorted(patches_dir.glob("*.md"))
            if patch_files:
                patches_note = f"\n\nCheck for review feedback in: {patches_dir}"

        prompt = (
            f"Implement the plan at: {plan_path}"
            f"{patches_note}"
        )

        if self.session_id:
            # Continuing — apply fixes from patches
            prompt = (
                f"Review feedback has been written to {patches_dir}. "
                f"Read the latest patch file there and apply the fixes."
            )

        _, self.session_id = _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt if not self.session_id else None,
            session_id=self.session_id,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )
