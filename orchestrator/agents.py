"""Agent runners — planner/reviewer and implementer via Claude Code CLI."""

from __future__ import annotations

import json
import signal
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
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, text=True,
                            start_new_session=True)

    # Ctrl+C kills the child and exits cleanly
    original_handler = signal.getsignal(signal.SIGINT)

    def _handle_sigint(signum, frame):
        proc.kill()
        proc.wait()
        print("\n>>> Interrupted by user")
        sys.exit(130)

    signal.signal(signal.SIGINT, _handle_sigint)
    try:
        stdout, _ = proc.communicate()
    finally:
        signal.signal(signal.SIGINT, original_handler)

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

    def review(self, plan_path: Path, patch_path: Path) -> bool:
        prompt = (
            f"Review the implementation against the plan at: {plan_path}\n"
            f"Run `git diff HEAD` and `git status` to see ALL changes (staged, unstaged, and new files).\n"
            f"Read each changed/new file to verify correctness — don't just look at the diff.\n"
            f"If issues found, write feedback to: {patch_path}\n"
            f"If everything looks good, respond with REVIEW_PASS\n"
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
