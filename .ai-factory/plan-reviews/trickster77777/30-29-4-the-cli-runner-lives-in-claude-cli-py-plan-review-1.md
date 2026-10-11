## Plan Review Summary

**Plan:** 29.4 — the CLI runner lives in `claude_cli.py`
**Files the plan touches:** 5 (`orchestrator/claude_cli.py` new, `orchestrator/agents.py`, `orchestrator/runtime.py`, `tests/test_agents.py`, `CLAUDE.md`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `.ai-factory/ARCHITECTURE.md` § Dependency Rules puts `claude_cli.py` in "Roles and adapters" and names the edges `agents` → `claude_cli` and `runtime` → `claude_cli`. The plan adds exactly those two edges. `claude_cli` imports only `state` and `errors`, which are both in the vocabulary layer, a downward import. That removes the `runtime` → `agents` edge, which is not a named edge. § Folder Structure gives `claude_cli.py` the job "resolving and launching the claude CLI, killing the active child, result classification, retries", and the moved set matches it. The anti-pattern "Launching the `claude` CLI anywhere but `claude_cli.py`" is satisfied for the runner. `usage.py` remains, and 29.5 handles it.
- **Rules — WARN.** `.ai-factory/RULES.md` is absent, so there are no explicit conventions to check against.
- **Roadmap — OK.** The plan matches contract line 29.4 in `.ai-factory/roadmaps/trickster77777.md` and its spec `.ai-factory/specs/trickster77777/0071-the-cli-runner-lives-in-claude-cli.md`, including every case under "What breaks on contact". The governing spec is ARCHITECTURE.md, and the plan cites the correct sections.

### Verification against the code

- **Moved names.** I checked every moved name against `orchestrator/agents.py`: `kill_active_child`, `MAX_RETRIES`, `RETRY_DELAY`, `_is_overloaded`, `_TRANSPORT_MARKERS`, `_is_transport_fault`, `_classify_result`, `_sorted_nvm_node_dirs`, `_resolve_claude`, `_CLAUDE_BIN` and `_run_claude`. The set is complete. `_load_prompt`, which sits between `kill_active_child` and `MAX_RETRIES` today, correctly stays in `agents`.
- **Imports leaving `agents`.** `json`, `os`, `signal`, `shutil`, `sys`, `state`, `NetworkError` and `RateLimitError` appear only in the moved code. I grepped the whole of `agents.py`: `signal` also appears as the identifier `pass_signal`, but not as the module. `subprocess`, `time` and `Path` are still used by `TestRunner.verify`, `PROMPTS_DIR` and the role signatures. `EscalationError` and `MissingArtifactError` are still raised by the roles.
- **Imports `claude_cli` needs.** The list `json, os, signal, shutil, subprocess, sys, time, Path, state, NetworkError, RateLimitError` covers every reference in the moved bodies.
- **`_run_claude` patches.** The roles call `_run_claude` through the `agents` global namespace. With `from .claude_cli import _run_claude`, `monkeypatch.setattr(agents, "_run_claude", ...)` in `_stub_run_claude_writing` and the two `MissingArtifactError` tests keeps intercepting them.
- **`runtime` patches.** `runtime._handle_sigint` calls the module-level `kill_active_child`. The `monkeypatch.setattr(runtime, "kill_active_child", ...)` patches in `tests/test_runtime.py` stay valid after the import source changes.
- **Test rewrites.** The planned rewrites in `tests/test_agents.py` match every current reference: `agents.shutil`, `agents.Path`, `agents._resolve_claude`, `agents._sorted_nvm_node_dirs`, `agents.os`, `agents._CLAUDE_BIN`, `agents.subprocess` and `agents._run_claude(...)` in the two `test_run_claude_*` tests. The `_classify_result` and `kill_active_child` imports are covered too. Patching `_CLAUDE_BIN` on `claude_cli` is required, not cosmetic, because `_run_claude` reads that global in its own module. No file in `tests/` other than `test_agents.py` reaches a moved name.
- **Unchanged modules.** `main.py`, `resume.py` and `usage.py` import no moved name, so they correctly stay out of scope.
- **Baseline.** `uv run pytest` passes 226 tests today. The plan's check "same test count as before" fits that baseline.
- **`CLAUDE.md`.** The edit targets the exact sentence in § Architecture ("`_run_claude()` in `agents.py` shells out…"). The role list stays correct, because the roles stay in `agents.py`.

### Critical Issues

None.

### Positive Notes

- The plan says which test patches stay, and explains why each one does (the caller's own namespace lookup). This is the subtle part of a module move, and the plan handles it carefully.
- The post-move `grep` check gives the implementer a mechanical way to confirm that no stale `agents.<moved>` reference remains.
- Keeping the definition order means `kill_active_child` is still defined before `_run_claude` uses it, which keeps the move a pure relocation.

## Deferred observations

- Affects: unknown (no roadmap task owns `docs/future/run-context-refactor.md`). After this move, that doc's "today" description becomes stale. It still says `active_proc` is "set in `agents._run_claude`, read/cleared in `agents.kill_active_child`", and its plan names `agents.py` as the module where `_run_claude`/`kill_active_child` stop writing to a global. Both now live in `claude_cli.py`. The spec for 29.4 limits the doc update to `CLAUDE.md` § Architecture, and the plan records this on purpose, so this task should not change the doc. Whoever next decomposes or revises the run-context refactor should point those references at `claude_cli`.

PLAN_REVIEW_PASS
