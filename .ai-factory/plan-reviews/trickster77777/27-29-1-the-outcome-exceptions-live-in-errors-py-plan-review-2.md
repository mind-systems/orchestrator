## Plan Review Summary

**Plan:** 29.1 — the outcome exceptions live in `errors.py`
**Task spec:** `.ai-factory/specs/trickster77777/0068-the-outcome-exceptions-live-in-errors.md` (governed by `.ai-factory/ARCHITECTURE.md` § Dependency Rules and § Folder Structure)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** ARCHITECTURE.md § Folder Structure lists `errors.py` as "Vocabulary: the outcome exceptions", and the layer table puts it in Vocabulary. The plan says the module imports nothing from the package. All the new edges point down: `agents` → `errors`, `main` → `errors` and `usage` → `errors`. The `usage` → `agents` edge, which the within-layer edge list never allowed, goes away.
- **Rules — WARN.** `.ai-factory/RULES.md` does not exist. There is also no `.ai-factory/skill-context/aif-review/SKILL.md`.
- **Roadmap — OK.** The plan matches contract line 29.1 in `.ai-factory/roadmaps/trickster77777.md` and its task spec 0068. It does not reach into 29.2–29.7: the protocol helpers, `VerifyKind` and the CLI runner all stay in `agents.py`.

### Ground-truth check (plan vs. code)

- `orchestrator/agents.py` defines the six classes in the stated order, between `_classify_result` and `_sorted_nvm_node_dirs`. The module already uses `from __future__ import annotations` and `from . import state`, which is where the plan anchors the new import. ✅
- `agents.py` raises only `NetworkError`, `RateLimitError`, `EscalationError` and `MissingArtifactError`. `HaltError` and `PipelineStopError` appear only in the class definitions and in the `EscalationError` docstring, and both of those move. So the four-name import is correct. ✅
- `main.py` imports `EscalationError`, `HaltError` and `PipelineStopError` from `agents` alongside the other names. `usage.py` imports only `HaltError` from `agents`. Both match the plan. ✅
- `tests/test_agents.py` imports through a parenthesized `from orchestrator.agents import (` block, and the four names the plan lists are in it. No test reads `agents.<Exception>` through the module object. ✅
- `tests/test_main.py` reads `getattr(agents_module, "HaltError", None)` in two tests, `test_check_usage_limits_raises_halt_error_over_threshold` and `test_process_task_resume_past_max_iterations_raises_halt_error`. `agents_module` has no other use in the file. The spec names only the first test. The plan's ground-truth note covers the second one, and it is correct. ✅
- `resume.py`, `runtime.py`, `notify.py` and `__init__.py` do not import any of the six names. `notify.py` mentions them only in comments. ✅
- No doc under `docs/` or in `CLAUDE.md` places these exceptions in `agents.py`, so no doc needs to change. ✅

### Prior-round finding

- Round 1 found that the grep-based check could not see a leftover import that is still resolvable through `agents`. The plan now uses an `ast` check of `ImportFrom` nodes and of `agents.`/`agents_module.` attribute reads. I ran that exact command against the current, unmodified tree. It reported all 12 current imports, including the 4 names inside the multi-line block in `tests/test_agents.py`, and exited 1. So the check does detect what it is meant to detect. The `'\\n'` inside the double-quoted bash string reaches Python as `'\n'`. A leftover `getattr(agents_module, …)` is not something the check sees, but once the `agents_module` import is removed that line raises `NameError`, so `pytest` catches it. ✅ Resolved.

### Critical Issues

None.

### Positive Notes

- The six classes are moved character-for-character and stay in the same order, including the `EscalationError` docstring that says it is "NOT a HaltError subclass". `test_escalation_error_is_not_halt_error` keeps guarding the hierarchy after the move.
- The "no re-export" rule is backed by the check itself, not just stated: `agents` imports only the names it raises, and the plan says to grep before adding any other name.
- The task dependencies are ordered correctly, and the plan correctly adds no test for a behaviour-neutral move.

PLAN_REVIEW_PASS
