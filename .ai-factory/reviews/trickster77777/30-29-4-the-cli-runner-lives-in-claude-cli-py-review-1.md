## Code Review Summary

**Files Reviewed:** 5 (`orchestrator/claude_cli.py` (new), `orchestrator/agents.py`, `orchestrator/runtime.py`, `tests/test_agents.py`, `CLAUDE.md`)
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture — OK.** `claude_cli.py` sits in the "Roles and adapters" layer. It imports only `state` and `errors` from the package, and both are vocabulary modules. The new edges are `agents` → `claude_cli` and `runtime` → `claude_cli`, and both are named edges in § Dependency Rules. The `runtime` → `agents` edge is gone. The only remaining importer of `agents` is `main`. `claude_cli.py` matches the § Folder Structure description: it resolves and launches the CLI, kills the active child, classifies results and runs retries.
- **Rules — OK.** `.ai-factory/RULES.md` does not exist, so this gate has nothing to check.
- **Roadmap — OK.** The change matches task 29.4 in `.ai-factory/roadmaps/trickster77777.md`, and every clause of spec `0071-the-cli-runner-lives-in-claude-cli.md` § What must be true after is met.

### Verification performed
- I compared the moved names byte for byte against `HEAD:orchestrator/agents.py`. The span from `kill_active_child` up to `_review_verifier`, minus `_load_prompt`, is identical to the body of `claude_cli.py` from `kill_active_child` to the end. The bodies and definition order are unchanged, so the move is behaviour-neutral.
- The new import blocks have no unused or missing names. `agents.py` keeps `subprocess`, `time` and `Path`, which `TestRunner.verify`, `PROMPTS_DIR` and the roles use, and it no longer refers to `os`, `json`, `sys`, `shutil`, `signal`, `state`, `NetworkError` or `RateLimitError`. `claude_cli.py` uses every import it declares.
- No `agents.<moved name>` reference is left in `orchestrator/` or `tests/`. The `agents._run_claude` patches still hold, because the roles look up `_run_claude` in the `agents` namespace. The `runtime.kill_active_child` patches in `tests/test_runtime.py` also still hold.
- `uv run pytest`: 226 passed. `tests/test_agents.py` has 65 test functions before and after the change, so no test was added or removed.

### Critical Issues

None.

### Positive Notes
- The move is purely mechanical. Bodies, docstrings, comments and ordering are preserved exactly, and `kill_active_child` is still defined before `_run_claude`.
- The stdlib patches (`shutil`, `Path`, `os`, `subprocess`) now name the module that actually makes the call, which is what the spec's "What breaks on contact" section asks for.
- The edit to `CLAUDE.md` is minimal: it changes only the module name in § Architecture.

## Deferred observations
- Affects: unknown (no roadmap task owns `docs/future/run-context-refactor.md`). That doc still describes `active_proc` as "set in `agents._run_claude`, read/cleared in `agents.kill_active_child`", and its plan names `agents.py` as the module whose `_run_claude`/`kill_active_child` stop writing to a global. Both functions now live in `claude_cli.py`. The 29.4 spec limits the doc update to `CLAUDE.md` § Architecture, so this task does not fix it. Whoever next revises or decomposes the run-context refactor should point those references at `claude_cli`.

REVIEW_PASS
