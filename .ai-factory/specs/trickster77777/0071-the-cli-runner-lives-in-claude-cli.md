# The CLI runner lives in claude_cli.py

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай декомпоуз 29» and «ставим и сохраняем»

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules and § Folder Structure.

What diverges now: [.ai-factory/specs/trickster77777/0067-modules-do-not-yet-follow-the-layer-map.md](0067-modules-do-not-yet-follow-the-layer-map.md).

## What is true now

This is the tree as the tasks above it leave it: the exceptions are in `errors.py`, the file protocol in `protocol.py`, the port and the kind type in `ports.py`.

`orchestrator/agents.py` holds the CLI runner beside the roles:

- `_CLAUDE_BIN`, `_sorted_nvm_node_dirs(dirs)` and `_resolve_claude() -> str`, which finds `claude` on `PATH` through `shutil.which` and otherwise under the versions of `Path.home() / ".nvm" / "versions" / "node"`;
- `_run_claude(prompt, cwd, system_prompt=None, allowed_tools=None, session_id=None, model=None, effort=None) -> tuple[str, str]`, which launches the child with `start_new_session=True`, tracks it in `state.active_proc`, parses the stream, retries, and calls `kill_active_child` on `KeyboardInterrupt`;
- `MAX_RETRIES`, `RETRY_DELAY`, `_is_overloaded`, `_TRANSPORT_MARKERS`, `_is_transport_fault` and `_classify_result`;
- `kill_active_child() -> None`.

`PROMPTS_DIR` and `_load_prompt` serve the roles. The roles call `_run_claude`. `runtime.py` imports `kill_active_child` from `agents`, and `_run_claude` calls it too. `CLAUDE.md` § Architecture says `_run_claude()` is in `agents.py`.

## What must be true after

A new `orchestrator/claude_cli.py` defines all of the above CLI-runner names, bodies unchanged, together with any import or constant only they use. It imports `errors` and `state` from the package. `PROMPTS_DIR` and `_load_prompt` stay in `agents`.

`agents` imports `_run_claude` from `claude_cli`, and `runtime` imports `kill_active_child` from `claude_cli`; the `runtime` → `agents` edge is gone. Tests that patch `shutil`, `Path`, `os`, `subprocess`, `_CLAUDE_BIN` or `_sorted_nvm_node_dirs` on `agents` patch `claude_cli` instead. `CLAUDE.md` § Architecture names `claude_cli.py` as the home of `_run_claude()`.

The change is behaviour-neutral: the command line, retries, classification and child handling are as before.

## What breaks on contact

- Tests that reach a moved name on `agents` move to `claude_cli`:
  - the `test_resolve_claude_*` tests patch `agents.shutil.which` and `agents.Path.home` and call `agents._resolve_claude`;
  - the `test_sorted_nvm_node_dirs_*` tests call `agents._sorted_nvm_node_dirs`;
  - the `test_kill_active_child_*` tests import `kill_active_child`, and `test_kill_active_child_falls_back_to_kill_on_killpg_failure` patches `agents.os.killpg`;
  - the `test_classify_result_*` tests import `_classify_result`;
  - `test_run_claude_ratelimit_halt_has_fixed_first_line` and `test_run_claude_launch_denies_work_outliving_the_turn` patch `agents._CLAUDE_BIN` and `agents.subprocess.Popen`.
- Left on `agents`, `_CLAUDE_BIN` and the direct calls raise `AttributeError`. The patches on `shutil`, `os`, `Path` and `subprocess` replace attributes of the stdlib modules themselves, so one left behind can keep intercepting while naming a module that no longer makes the call; they move so the name matches the owner.
- Patches the callers still look up in their own module stay valid: `agents._run_claude` in `_stub_run_claude_writing`, `test_review_missing_file_raises_missing_artifact_error` and `test_review_plan_missing_file_raises_missing_artifact_error` (the roles import `_run_claude` into `agents`), and `runtime.kill_active_child` in the `test_handle_sigint_second_press_*` tests (`runtime` imports it into its own namespace).
