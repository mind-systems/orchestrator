# Plan: 29.4 — the CLI runner lives in `claude_cli.py`

## Context
Move the Claude CLI runner out of `agents.py` into a new adapter module `orchestrator/claude_cli.py`. The runner is resolving, launching, classifying, retrying and killing the child. After the move, `runtime` takes `kill_active_child` from `claude_cli`, so the `runtime` → `agents` edge is gone. This is behaviour-neutral and adds no new test. Spec: `.ai-factory/specs/trickster77777/0071-the-cli-runner-lives-in-claude-cli.md`. Governing spec: `.ai-factory/ARCHITECTURE.md`. Its § Dependency Rules places `claude_cli.py` in the "Roles and adapters" layer, with the named edges `agents` → `claude_cli` and `runtime` → `claude_cli`. Its § Folder Structure says `claude_cli.py` resolves and launches the claude CLI, kills the active child, classifies results and runs retries.

Notes from the code:
- After the move, `agents.py` still uses `subprocess` and `time` in `TestRunner.verify` (`time.monotonic`, `subprocess.run`, `subprocess.PIPE`/`STDOUT`). It uses `Path` for `PROMPTS_DIR` and the role signatures, and `EscalationError`/`MissingArtifactError` in the roles. Those imports stay.
- `json`, `os`, `signal`, `shutil` and `sys`, the `from . import state` import, and `NetworkError`/`RateLimitError` are used only by the moved names. They leave `agents`.
- Nothing in `main.py`, `resume.py` or `usage.py` imports a moved name, so those modules do not change.
- `docs/future/run-context-refactor.md` still cites `agents._run_claude`/`agents.kill_active_child`. The spec scopes the doc update to `CLAUDE.md` § Architecture only, so that future doc is left as it is.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Adapter module

- [x] **Create `orchestrator/claude_cli.py` with the CLI runner**
  Files: `orchestrator/claude_cli.py`
  Follow the header shape of the sibling modules: a one-line module docstring (e.g. `"""Claude CLI adapter — resolving and launching the claude CLI, classifying results, retries, and killing the active child."""`), then `from __future__ import annotations`. Then the stdlib imports the moved code uses: `json`, `os`, `signal`, `shutil`, `subprocess`, `sys`, `time`, `from pathlib import Path`. Then the package imports `from . import state` and `from .errors import NetworkError, RateLimitError`, and nothing else from the package.
  Move these from `agents.py` verbatim, with bodies, docstrings, comments and module-level values unchanged:
  - `kill_active_child() -> None`
  - `MAX_RETRIES = 3`, `RETRY_DELAY = 30  # seconds`
  - `_is_overloaded`, `_TRANSPORT_MARKERS`, `_is_transport_fault`, `_classify_result`
  - `_sorted_nvm_node_dirs`, `_resolve_claude`
  - `_CLAUDE_BIN: str | None = None`
  - `_run_claude(...)`, including its `global _CLAUDE_BIN` lazy resolution, `state.active_proc` tracking, and the `kill_active_child()` call on `KeyboardInterrupt`
  Keep the order they have in `agents.py` today, so `kill_active_child` is defined before `_run_claude`.

### Rewire importers

- [x] **Strip the runner from `agents.py`** (depends on Create `orchestrator/claude_cli.py`)
  Files: `orchestrator/agents.py`
  Delete every name moved above. Keep `PROMPTS_DIR` and `_load_prompt` in place. Add `from .claude_cli import _run_claude` and re-export nothing else from `claude_cli`. Drop the imports that only the moved code used: `json`, `os`, `signal`, `shutil`, `sys`, `from . import state`, and `NetworkError, RateLimitError` from the `.errors` import, which becomes `from .errors import EscalationError, MissingArtifactError`. Keep `subprocess`, `time` and `Path`, which `TestRunner` and the roles still use. The role call sites `_run_claude(...)` stay textually unchanged and resolve through the module-level import, so `monkeypatch.setattr(agents, "_run_claude", ...)` keeps intercepting them. If the module docstring still mentions the CLI, it may say only that the roles run through the Claude Code CLI; no other wording changes.

- [x] **Point `runtime.py` at `claude_cli`** (depends on Create `orchestrator/claude_cli.py`)
  Files: `orchestrator/runtime.py`
  Replace `from .agents import kill_active_child` with `from .claude_cli import kill_active_child`. Nothing else changes: `_handle_sigint` still calls the module-level name, so `monkeypatch.setattr(runtime, "kill_active_child", ...)` in `tests/test_runtime.py` stays valid.

### Tests follow the owner

- [x] **Move the moved-name patches and imports in `tests/test_agents.py` to `claude_cli`** (depends on Strip the runner from `agents.py`)
  Files: `tests/test_agents.py`
  - Imports: change `from orchestrator import agents, state` to `from orchestrator import agents, claude_cli, state`. Remove `_classify_result` and `kill_active_child` from the `from orchestrator.agents import (...)` block, and add `from orchestrator.claude_cli import _classify_result, kill_active_child`.
  - `test_resolve_claude_*`: `agents.shutil` → `claude_cli.shutil`, `agents.Path` → `claude_cli.Path`, `agents._resolve_claude()` → `claude_cli._resolve_claude()`.
  - `test_sorted_nvm_node_dirs_*`: `agents._sorted_nvm_node_dirs` → `claude_cli._sorted_nvm_node_dirs`.
  - `test_kill_active_child_falls_back_to_kill_on_killpg_failure`: `agents.os` → `claude_cli.os`.
  - `test_run_claude_ratelimit_halt_has_fixed_first_line` and `test_run_claude_launch_denies_work_outliving_the_turn`: `monkeypatch.setattr(agents, "_CLAUDE_BIN", ...)` → `monkeypatch.setattr(claude_cli, "_CLAUDE_BIN", ...)`, `agents.subprocess` → `claude_cli.subprocess`, `agents._run_claude(...)` → `claude_cli._run_claude(...)`.
  - Leave these unchanged: the `monkeypatch.setattr(agents, "_run_claude", ...)` patches in `_stub_run_claude_writing`, `test_review_missing_file_raises_missing_artifact_error` and `test_review_plan_missing_file_raises_missing_artifact_error`. They patch the roles' own lookup. Also leave every test that uses `os`/`subprocess`/`time` directly rather than through a module, such as `test_kill_active_child_kills_live_process_group`. No test is added, removed or reworded beyond these references.
  - Then run `grep -nE 'agents\.(shutil|Path|os|subprocess|_CLAUDE_BIN|_sorted_nvm_node_dirs|_resolve_claude|_classify_result|kill_active_child|MAX_RETRIES|RETRY_DELAY|_is_overloaded|_is_transport_fault|_TRANSPORT_MARKERS)' tests/` and expect no matches. Run `uv run pytest` and expect it to pass with the same test count as before.

### Docs

- [x] **Name `claude_cli.py` as the home of `_run_claude()` in `CLAUDE.md`** (depends on Strip the runner from `agents.py`)
  Files: `CLAUDE.md`
  In § Architecture, change the sentence "`_run_claude()` in `agents.py` shells out to the `claude` CLI …" to "`_run_claude()` in `claude_cli.py` shells out to the `claude` CLI …". Leave the rest of that sentence and the role list (`PlannerReviewer`/`PlanReviewer`/`Implementer`/`TestRunner` in `agents.py`) unchanged.
