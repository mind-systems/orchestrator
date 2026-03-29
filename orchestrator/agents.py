"""Agent runners — planner/reviewer and implementer via Claude Code CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import state

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


MAX_RETRIES = 3
RETRY_DELAY = 30  # seconds


class RateLimitError(Exception):
    """Raised when the Claude API rate limit / daily quota is exhausted."""


class PipelineStopError(Exception):
    """Raised to request a graceful halt of the pipeline."""


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

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n--- Claude agent ({cwd}) ---")
        start = time.monotonic()
        proc = subprocess.Popen(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            start_new_session=True,
        )

        try:
            stdout, stderr = proc.communicate()
        except KeyboardInterrupt:
            # Second Ctrl+C while waiting — kill immediately
            proc.kill()
            proc.wait()
            print("\n>>> Force quit.")
            sys.exit(130)

        elapsed = int(time.monotonic() - start)
        mins, secs = divmod(elapsed, 60)

        # Check for retryable errors (overloaded, rate limit)
        retryable = False
        if proc.returncode != 0 and stdout:
            try:
                parsed = json.loads(stdout)
                result_text = parsed.get("result", "")
                if "overloaded" in result_text.lower() or "529" in result_text:
                    retryable = True
            except json.JSONDecodeError:
                pass

        if retryable and attempt < MAX_RETRIES:
            print(f">>> API overloaded, retrying in {RETRY_DELAY}s (attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            continue

        if proc.returncode != 0:
            # Even on non-zero exit, stdout may contain a structured error
            if stdout:
                try:
                    parsed = json.loads(stdout)
                    result_text = parsed.get("result", "")
                    if "hit your limit" in result_text.lower() or "resets" in result_text.lower():
                        raise RateLimitError(result_text)
                except (json.JSONDecodeError, KeyError):
                    pass
            raise RuntimeError(
                f"Claude CLI failed with exit code {proc.returncode}\n"
                f"stderr: {stderr[:1000] if stderr else '(empty)'}\n"
                f"stdout: {stdout[:1000] if stdout else '(empty)'}"
            )

        if not stdout.strip():
            raise RuntimeError(
                f"Claude CLI exited 0 but stdout is empty\n"
                f"stderr: {stderr[:1000] if stderr else '(empty)'}"
            )

        parsed = json.loads(stdout)
        if parsed.get("is_error"):
            result_text = parsed.get("result", "")
            if "hit your limit" in result_text.lower() or "resets" in result_text.lower():
                raise RateLimitError(result_text)
            if ("overloaded" in result_text.lower() or "529" in result_text) and attempt < MAX_RETRIES:
                print(f">>> API overloaded, retrying in {RETRY_DELAY}s (attempt {attempt}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY)
                continue
            raise RuntimeError(f"Claude returned error: {result_text[:500]}")

        output_text = parsed.get("result", "")
        sid = parsed.get("session_id", "")

        summary = output_text[:500] + ("..." if len(output_text) > 500 else "")
        print(f"{summary}\n  [{mins}m {secs}s]")

        return output_text, sid

    # Should never reach here, but just in case
    raise RuntimeError("All retry attempts exhausted")


class PlannerReviewer:
    """Plans and reviews milestones. Same session — reviewer has planner's context."""

    def __init__(
        self,
        project_dir: Path,
        model: str = "opus",
        effort: str = "high",
    ):
        self.project_dir = project_dir
        self.planner_prompt = _load_prompt("planner")
        self.reviewer_prompt = _load_prompt("reviewer")
        self.system_prompt = self.planner_prompt + "\n\n---\n\n" + self.reviewer_prompt
        self.session_id: str | None = None
        self.tools = ["Read", "Write", "Glob", "Grep", "Bash"]
        self.model = model
        self.effort = effort

    def plan(self, milestone_title: str, milestone_description: str, plan_path: Path, feedback: str | None = None) -> None:
        if feedback:
            prompt = (
                f"Your plan at {plan_path} was reviewed and has issues.\n\n"
                f"Reviewer feedback:\n{feedback}\n\n"
                f"Update the plan to address these issues. Write the updated plan to: {plan_path}\n"
            )
        else:
            prompt = (
                f"Create an implementation plan for this milestone:\n\n"
                f"**{milestone_title}**\n"
                f"{milestone_description}\n\n"
                f"Write the plan to: {plan_path}\n"
            )

        _, self.session_id = _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )

    def review(self, plan_path: Path, review_path: Path) -> bool:
        """Review code changes. Uses same session as planner for deep context."""
        prompt = (
            f"The plan for context is at: {plan_path}\n"
            f"Review the CODE CHANGES for bugs, security issues, and correctness problems.\n"
            f"Run `git diff HEAD` and `git status` to see ALL changes.\n"
            f"Read each changed/new file IN FULL — understand the surrounding code, not just the diff.\n"
            f"Think about what will break at runtime: missing migrations, type mismatches, race conditions, etc.\n"
            f"Write your full review to: {review_path}\n"
            f"If no critical issues found, end the review file with REVIEW_PASS on its own line.\n"
        )

        output, self.session_id = _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt if not self.session_id else None,
            session_id=self.session_id,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )

        # Check the review file, not the chat output — look for REVIEW_PASS on its own line
        if review_path.exists():
            review_text = review_path.read_text()
            return review_text.strip().endswith("REVIEW_PASS")
        return False

    def patch(self, review_path: Path, patch_path: Path) -> None:
        """Read a review and create a detailed patch for the implementer."""
        prompt = (
            f"Read the review at: {review_path}\n"
            f"Create a detailed implementation patch that describes exactly what needs to be fixed.\n"
            f"For each issue, specify the file, the problem, and the exact fix.\n"
            f"Write the patch to: {patch_path}\n"
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


class PlanReviewer:
    """Reviews a plan before implementation. Fresh session — no planner bias."""

    def __init__(
        self,
        project_dir: Path,
        model: str = "opus",
        effort: str = "high",
    ):
        self.project_dir = project_dir
        self.system_prompt = _load_prompt("reviewer")
        self.tools = ["Read", "Glob", "Grep", "Bash"]
        self.model = model
        self.effort = effort

    def review_plan(self, plan_path: Path) -> tuple[bool, str]:
        """Review a plan file. Returns (passed, feedback_text)."""
        prompt = (
            f"Review the PLAN at: {plan_path}\n"
            f"Read the plan file and the codebase it targets.\n"
            f"Check for: missing steps, wrong assumptions about the codebase, "
            f"architectural mistakes, missing migrations, security issues, "
            f"incorrect file paths or API usage.\n"
            f"Do NOT write to a file. Just output your review.\n"
            f"If the plan is solid, end your response with REVIEW_PASS on its own line.\n"
        )

        output, _ = _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )

        passed = output.strip().endswith("REVIEW_PASS")
        return passed, output


class Implementer:
    """Implements the plan, then applies fixes from patches. Same session."""

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
