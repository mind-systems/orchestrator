## Code Review Summary

**Files Reviewed:** 6 (`orchestrator/errors.py` is new; `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/usage.py`, `tests/test_agents.py` and `tests/test_main.py` are modified)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `.ai-factory/ARCHITECTURE.md` § Folder Structure gives `errors.py` as "Vocabulary: the outcome exceptions". The new module imports nothing from the package, as § Dependency Rules requires for the vocabulary layer. All the new edges point down: `agents` → `errors`, `main` → `errors` and `usage` → `errors`. `usage` no longer imports `agents`, so the edge that § Dependency Rules never named is gone.
- **Rules — WARN.** `.ai-factory/RULES.md` does not exist. There is also no `.ai-factory/skill-context/aif-review/SKILL.md`.
- **Roadmap — OK.** The diff matches contract line 29.1 in `.ai-factory/roadmaps/trickster77777.md` and its task spec `0068-the-outcome-exceptions-live-in-errors.md`. It stays out of 29.2–29.5: the protocol helpers, `VerifyKind` and the CLI runner are still in `agents.py`.

### Verification performed

- **The move is exact.** I compared the six classes removed from `agents.py` with the six added to `errors.py`. Bases, docstrings and order are character-for-character identical, including `EscalationError` as a direct `Exception` subclass with its "NOT a HaltError subclass" note.
- **No re-export.** `agents.py` imports only `EscalationError`, `MissingArtifactError`, `NetworkError` and `RateLimitError`, which are the names it raises. Neither `HaltError` nor `PipelineStopError` appears in it, and there is no `__all__` and no alias.
- **No leftover imports.** I ran the plan's `ast` check, which reads `from … agents import` statements and `agents.`/`agents_module.` attribute reads across `orchestrator/` and `tests/`. It printed nothing and exited 0, and it covers the multi-line import block in `tests/test_agents.py`.
- **`usage.py` no longer mentions `agents`.**
- **Both `getattr` reads switched.** `tests/test_main.py` now reads `HaltError` from `errors_module` in both tests that used `agents_module`: the one the spec names and `test_process_task_resume_past_max_iterations_raises_halt_error`, which the plan's ground-truth note added. With no re-export, both would have failed, so switching both is correct. `agents_module` had no other use, and its import is replaced.
- **No stale docs.** No doc in `docs/`, `CLAUDE.md`, `README.md` or `AGENTS.md` places these exceptions in `agents.py`.
- **Tests pass.** `uv run pytest` reports 226 passed. No test was added and no assertion was changed.
- **Behaviour is unchanged.** Exception identity is preserved: one class object per name, reached from every importer. So the `except HaltError` / `except EscalationError` / `except PipelineStopError` branches in `main.cli()` and the notification mapping behave exactly as before.

### Critical Issues

None.

### Positive Notes

- The import list in `agents.py` is limited to the names actually raised, so a missed importer fails loudly instead of resolving through `agents`. This is the failure the spec warns about.
- The second `getattr(agents_module, …)` read was found in the code rather than taken from the spec, and the plan records why it changed.
- The diff is minimal: only import lines change outside the moved block.

REVIEW_PASS
