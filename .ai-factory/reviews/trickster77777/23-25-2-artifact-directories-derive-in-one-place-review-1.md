## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/main.py`, `tests/test_main.py`)
**Risk Level:** 🟢 Low

### Context Gates
- Architecture: OK. `.ai-factory/ARCHITECTURE.md` § What varies (Layout) says every artifact directory derives in one place from the subdirectory chosen at assembly. After this change `_artifact_dir` is the only place that joins `artifact_subdir`. `_implement_loop` and `_test_loop` still assemble the mode as § Composition root requires. The other `project_dir / ".ai-factory" / …` joins in `main.py` and `config.py` build roadmap and config-overlay paths, not artifact directories.
- Rules: WARN. `.ai-factory/RULES.md` does not exist, so this gate has nothing to check.
- Roadmap: OK. The change matches 25.2 in `roadmaps/trickster77777.md` and its spec `0061-artifact-directories-derive-in-one-place.md`. Each "What must be true after" item is met:
  - `_artifact_dir` has the signature the spec gives.
  - `process_task` gets its plans, output and plan-reviews directories from `_artifact_dir`, and its `mkdir` calls are unchanged.
  - `_run_dynamic_loop` takes `mode: Mode` instead of `artifact_subdir`, still creates only the plans directory, and both callers pass `mode=mode`.
  - The spec's three test cases are present.
- Skill context: `.ai-factory/skill-context/aif-review/SKILL.md` does not exist.

### Critical Issues
None.

Things I checked:
- **Same behaviour.** `_artifact_dir` uses the same truthiness test as the old `if mode.artifact_subdir:` blocks, so a flat mode (`None`) and the named-roadmap case give the same paths as before. The function never creates a directory, and the `mkdir` calls run in the same order and at the same points as before. That means directory creation is also unchanged, as the spec requires.
- **Names and annotations resolve.** `Mode` is defined before `_artifact_dir`, and `from __future__ import annotations` is in effect, so the annotations resolve.
- **Callers.** Nothing else calls `_run_dynamic_loop` (`notify.py` only names it in comments). The new `mode` parameter has no default, which matches its only two callers.
- **Leftover references.** No docs, `CLAUDE.md` or `ARCHITECTURE.md` mention the removed `artifact_subdir` parameter.
- **Test suite.** `uv run pytest` gives 227 passed. The new tests compare against literal `.ai-factory/plans`, `.ai-factory/plans/john-doe` and `.ai-factory/test-runs` paths, so they would catch the silent wrong-join failure the spec describes. The first test also checks that no directory is created.

### Positive Notes
- The duplicated join is gone completely. Changing the layout now means editing one function, which is the "a choice is held once" rule in ARCHITECTURE.md § The rule.
- The docstring describes behaviour and has no plan-layer references.
- The tests match the existing `_artifact_subdir` section's banner and "Should …" docstring style, and the `_artifact_subdir` tests are untouched.

REVIEW_PASS
