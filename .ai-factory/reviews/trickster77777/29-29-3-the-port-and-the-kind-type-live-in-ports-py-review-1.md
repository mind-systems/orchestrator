## Code Review Summary

**Files Reviewed:** 5 (`orchestrator/ports.py` new; `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/resume.py`, `tests/test_main.py` modified)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.**
  - `ports.py` imports only `pathlib` and `typing`. Nothing comes from the package, at runtime or under `TYPE_CHECKING`. This matches the vocabulary rule in ARCHITECTURE.md § Dependency Rules.
  - `make_verifier` is now `Callable[[VerifierProtocol, Path], VerifierProtocol]`, so the role-name annotation edge is gone.
  - `resume` (the flow) imports only `ports` and `protocol`, so the `resume` → `agents` edge is removed.
  - `agents` → `ports` and `main` → `ports` both point downward.
  - `agents` re-exports nothing.
  - The module now matches the § Folder Structure entry `ports.py — Vocabulary: VerifierProtocol and the VerifyKind type`.
- **Rules — OK / WARN.** There is no `.ai-factory/RULES.md` (WARN: the optional file is missing). No skill-context file exists for aif-review.
- **Roadmap — OK.** The change matches the contract line 29.3 in `.ai-factory/roadmaps/trickster77777.md` and its spec `0070-the-port-and-the-kind-type-live-in-ports.md`:
  - **Moved as-is:** the port and the type move with bodies, field order and comments unchanged.
  - **Retyped:** only the `make_verifier` annotation changes. The factories' reviewer parameter is now typed `VerifierProtocol`.
  - **Kept in `agents`:** `REVIEW_VERIFY` and `TEST_RUN_VERIFY` stay there.
  - **Wrappers moved:** the two wrappers are deleted from `resume`. They come back as helpers in `tests/test_main.py` with the same names, signatures and behaviour, passing the kinds imported from `agents`.
  - **The plan's one assumption:** `main` imports only `VerifyKind` from `ports`, because it never names `VerifierProtocol`. This is a reasonable reading of the spec, since edges are directions, not inventories.

### Critical Issues

None.

Verification performed:
- **Old import sites:** `grep` finds no remaining imports of `VerifyKind`/`VerifierProtocol` from `agents`, and no `_detect_task_step`/`_detect_test_task_step` anywhere under `orchestrator/`.
- **Unused imports:** nothing left in `agents.py` uses `Callable`, `NamedTuple` or `Protocol`, so removing the `typing` import is correct. `Path | None` in signatures is safe under `from __future__ import annotations`.
- **Runtime behaviour:**
  - `process_task` still calls `mode.verify.make_verifier(planner_reviewer, project_dir)`, and `PlannerReviewer` satisfies the port structurally.
  - Step values, fail tags, suffixes and pass signals in `REVIEW_VERIFY`/`TEST_RUN_VERIFY` are unchanged.
  - `_detect_step` in `resume.py` is untouched.
- **Docs:** none of `docs/`, `CLAUDE.md` or `README.md` name the moved symbols or the removed wrappers.
- **Tests:** `uv run pytest` gives 226 passed. The `test_detect_task_step_*` and `test_detect_test_task_step_*` bodies are unchanged and call the local helpers. The test module docstring still names both helpers and is still accurate.

### Positive Notes

- Clean, minimal move: the diff is exactly the planned surface, with no gold-plating.
- `ports.py` follows the header shape of its sibling vocabulary modules (`errors.py`, `protocol.py`).
- The relative imports stay alphabetical in `agents.py` and `main.py`.
- The test helpers keep their original names and signatures, so no test body had to change. That keeps the move behaviour-neutral and easy to audit.

REVIEW_PASS
