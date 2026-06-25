"""Agent runners — planner/reviewer and implementer via Claude Code CLI."""

from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import state

PROMPTS_DIR = Path(__file__).parent / "prompts"


def kill_active_child() -> None:
    """Kill the in-flight Claude CLI child process group, if any."""
    proc = state.active_proc
    if proc is None or proc.poll() is not None:
        state.active_proc = None
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except Exception:
            pass
    state.active_proc = None


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


MAX_RETRIES = 3
RETRY_DELAY = 30  # seconds

def _has_signal(text: str, signal: str) -> bool:
    """Return True if signal appears as an exact line within the last 5 lines."""
    return any(line.strip() == signal for line in text.splitlines()[-5:])


def _read_sessions(plan_path: Path) -> dict[str, str]:
    p = plan_path.with_suffix('.json')
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_session(plan_path: Path, key: str, value: str) -> None:
    p = plan_path.with_suffix('.json')
    try:
        data = json.loads(p.read_text()) if p.exists() else {}
    except (json.JSONDecodeError, OSError):
        data = {}
    data[key] = value
    tmp = p.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, p)


class RateLimitError(Exception):
    """Raised when the Claude API rate limit / daily quota is exhausted."""


class PipelineStopError(Exception):
    """Raised to request a graceful halt of the pipeline."""


def _resolve_claude() -> str:
    """Return the absolute path to the claude CLI, or raise if not found."""
    path = shutil.which("claude")
    if path:
        return path
    # nvm installs into a versioned directory that may not be in a subprocess PATH
    nvm_base = Path.home() / ".nvm" / "versions" / "node"
    if nvm_base.is_dir():
        for node_dir in sorted(nvm_base.iterdir(), reverse=True):
            candidate = node_dir / "bin" / "claude"
            if candidate.exists():
                return str(candidate)
    raise FileNotFoundError(
        "claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
    )


_CLAUDE_BIN: str | None = None


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
    global _CLAUDE_BIN
    if _CLAUDE_BIN is None:
        _CLAUDE_BIN = _resolve_claude()

    if allowed_tools is None:
        allowed_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]

    cmd = [
        _CLAUDE_BIN,
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
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
        state.active_proc = proc

        lines: list[str] = []
        sid_seen: str = ""

        try:
            for line in proc.stdout:  # type: ignore[union-attr]
                line = line.rstrip("\n")
                lines.append(line)
                if not sid_seen and line:
                    try:
                        event = json.loads(line)
                        s = event.get("session_id", "")
                        if s:
                            sid_seen = s
                            print(f"  [session: {sid_seen}]")
                    except json.JSONDecodeError:
                        pass
        except KeyboardInterrupt:
            kill_active_child()
            if sid_seen:
                print(f"\n>>> Interrupted — session: {sid_seen}")
            else:
                print("\n>>> Interrupted (session_id not yet received).")
            sys.exit(130)

        proc.wait()
        state.active_proc = None
        stderr = proc.stderr.read() if proc.stderr else ""  # type: ignore[union-attr]
        stdout = "\n".join(lines)

        elapsed = int(time.monotonic() - start)
        mins, secs = divmod(elapsed, 60)

        # Find the final result event (last line with "result" key)
        parsed_final: dict = {}
        for line in reversed(lines):
            if not line:
                continue
            try:
                ev = json.loads(line)
                if "result" in ev:
                    parsed_final = ev
                    break
            except json.JSONDecodeError:
                continue

        result_text = parsed_final.get("result", "")
        is_error = parsed_final.get("is_error", False)

        # Check for retryable errors (overloaded, rate limit)
        retryable = (
            "overloaded" in result_text.lower() or "529" in result_text
        ) and attempt < MAX_RETRIES

        if retryable:
            print(f">>> API overloaded, retrying in {RETRY_DELAY}s (attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            continue

        if proc.returncode != 0:
            if "hit your limit" in result_text.lower() or "resets" in result_text.lower():
                raise RateLimitError(result_text)
            raise RuntimeError(
                f"Claude CLI failed with exit code {proc.returncode}\n"
                f"stderr: {stderr if stderr else '(empty)'}\n"
                f"stdout: {stdout if stdout else '(empty)'}"
            )

        if not lines:
            raise RuntimeError(
                f"Claude CLI exited 0 but stdout is empty\n"
                f"stderr: {stderr[:1000] if stderr else '(empty)'}"
            )

        if is_error:
            if "hit your limit" in result_text.lower() or "resets" in result_text.lower():
                raise RateLimitError(result_text)
            raise RuntimeError(f"Claude returned error: {result_text[:500]}")

        sid = parsed_final.get("session_id", sid_seen)
        if not sid_seen:
            # session_id only in final event — print it now
            print(f"  [session: {sid}]")

        summary = result_text[:500] + ("..." if len(result_text) > 500 else "")
        print(f"{summary}\n  [{mins}m {secs}s]")

        return result_text, sid

    raise RuntimeError("All retry attempts exhausted")


class PlannerReviewer:
    """Plans and reviews milestones. Same session — reviewer has planner's context."""

    def __init__(
        self,
        project_dir: Path,
        model: str = "opus",
        effort: str = "high",
        planner_prompt_name: str = "planner",
    ):
        self.project_dir = project_dir
        self.planner_prompt = _load_prompt(planner_prompt_name)
        self.reviewer_prompt = _load_prompt("reviewer")
        self.system_prompt = self.planner_prompt + "\n\n---\n\n" + self.reviewer_prompt
        self.session_id: str | None = None
        self.tools = ["Read", "Write", "Glob", "Grep", "Bash"]
        self.model = model
        self.effort = effort

    def plan(self, milestone_title: str, milestone_description: str, plan_path: Path, plan_review_path: Path | None = None, roadmap_path: Path | None = None, line_number: int | None = None) -> None:
        if plan_review_path:
            prompt = (
                f"Your plan at {plan_path} was reviewed and has issues.\n\n"
                f"Read the review at: {plan_review_path}\n\n"
                f"Update the plan to address the issues in that review. Write the updated plan to: {plan_path}\n"
            )
        else:
            roadmap_line = ""
            if roadmap_path is not None and line_number is not None:
                roadmap_line = f"Roadmap: {roadmap_path} (line {line_number + 1})\n"
            prompt = (
                f"Create an implementation plan for this milestone:\n\n"
                f"{roadmap_line}"
                f"**{milestone_title}**\n"
                f"{milestone_description}\n\n"
                f"Write the plan to: {plan_path}\n"
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
        _write_session(plan_path, "planner", self.session_id)

    def review(self, plan_path: Path, review_path: Path) -> bool:
        """Review code changes. Uses same session as planner for deep context."""
        prompt = (
            f"The plan for context is at: {plan_path}\n"
            f"Review the CODE CHANGES for bugs, security issues, and correctness problems.\n"
            f"Run `git diff HEAD` and `git status` to see ALL changes.\n"
            f"Read each changed/new file IN FULL — understand the surrounding code, not just the diff.\n"
            f"Think about what will break at runtime: missing migrations, type mismatches, race conditions, etc.\n"
            f"Write your full review to: {review_path}\n"
            f"If you have no findings at all, end the review file with REVIEW_PASS on its own line.\n"
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
        _write_session(plan_path, "planner", self.session_id)

        # Check the review file, not the chat output — look for REVIEW_PASS on its own line
        if review_path.exists():
            return _has_signal(review_path.read_text(), "REVIEW_PASS")
        return False


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
        self.tools = ["Read", "Write", "Glob", "Grep", "Bash"]
        self.model = model
        self.effort = effort

    def review_plan(self, plan_path: Path, review_path: Path) -> bool:
        """Review a plan file. Writes review to review_path. Returns True if passed."""
        prompt = (
            f"Review the PLAN at: {plan_path}\n"
            f"Read the plan file and the codebase it targets.\n"
            f"Check for: missing steps, wrong assumptions about the codebase, "
            f"architectural mistakes, missing migrations, security issues, "
            f"incorrect file paths or API usage.\n"
            f"Write your full review to: {review_path}\n"
            f"If the plan is solid, end the review file with PLAN_REVIEW_PASS on its own line.\n"
        )

        _, sid = _run_claude(
            prompt=prompt,
            cwd=str(self.project_dir),
            system_prompt=self.system_prompt,
            allowed_tools=self.tools,
            model=self.model,
            effort=self.effort,
        )
        if review_path.exists():
            return _has_signal(review_path.read_text(), "PLAN_REVIEW_PASS")
        return False


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

    def implement(self, plan_path: Path, patches_dir: Path, roadmap_path: Path | None = None, line_number: int | None = None) -> None:
        if self.session_id:
            # Continuing — apply fixes from patches
            prompt = (
                f"Review feedback has been written to {patches_dir}. "
                f"Read the latest patch file there and apply the fixes."
            )
        else:
            patches_note = ""
            if patches_dir.exists():
                patch_files = sorted(patches_dir.glob("*.md"))
                if patch_files:
                    patches_note = f"\n\nCheck for review feedback in: {patches_dir}"

            roadmap_line = ""
            if roadmap_path is not None and line_number is not None:
                roadmap_line = f"Roadmap: {roadmap_path} (line {line_number + 1})\n"

            prompt = (
                f"{roadmap_line}"
                f"Implement the plan at: {plan_path}"
                f"{patches_note}"
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
        _write_session(plan_path, "implementer", self.session_id)


class TestRunner:
    """Runs the test command from the plan file and captures output. No LLM."""

    def run(self, plan_path: Path, output_path: Path, project_dir: Path) -> bool:
        """Extract test command from plan, run it, write output. Returns True if exit code 0."""
        cmd = self._extract_test_command(plan_path)
        if not cmd:
            output_path.write_text("ERROR: No '## Test Command' section found in plan.\n")
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\n--- TestRunner: {cmd} ---")
        start = time.monotonic()
        result = subprocess.run(
            cmd, shell=True, cwd=str(project_dir),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        elapsed = time.monotonic() - start
        output = (
            f"$ {cmd}\n"
            f"exit code: {result.returncode}\n"
            f"elapsed: {elapsed:.1f}s\n\n"
            f"{result.stdout}"
        )
        passed = result.returncode == 0
        if passed:
            output += "\nTEST_PASS"
        output_path.write_text(output)
        status = "PASSED" if passed else "FAILED"
        print(f"--- TestRunner: {status} (exit {result.returncode}, {elapsed:.1f}s) ---")
        return passed

    @staticmethod
    def _extract_test_command(plan_path: Path) -> str | None:
        """Read `## Test Command` section from the plan and return the command string."""
        lines = plan_path.read_text().splitlines()
        in_section = False
        for line in lines:
            if line.strip() == "## Test Command":
                in_section = True
                continue
            if in_section:
                stripped = line.strip()
                if stripped.startswith("#"):
                    break
                if stripped.startswith("`") and stripped.endswith("`"):
                    return stripped.strip("`")
                if stripped:
                    return stripped
        return None
