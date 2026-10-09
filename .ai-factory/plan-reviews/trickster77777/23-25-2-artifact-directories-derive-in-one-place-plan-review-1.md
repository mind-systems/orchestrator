## Plan Review Summary

**Plan:** `.ai-factory/plans/trickster77777/23-25-2-artifact-directories-derive-in-one-place.md`
**Task:** 25.2 — artifact directories derive in one place (`.ai-factory/roadmaps/trickster77777.md`)
**Spec:** `.ai-factory/specs/trickster77777/0061-artifact-directories-derive-in-one-place.md`
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture** — OK. `.ai-factory/ARCHITECTURE.md` § What varies, under the **Layout** bullet, says every artifact directory derives "in one place" from the artifact subdirectory, which is derived once at assembly. § The rule says "a choice is held once". The plan does both: `_artifact_dir` becomes the single place the subdirectory is joined, and `_run_dynamic_loop` reads it from the mode instead of from a second parameter. § Composition root stays the same: `_implement_loop` and `_test_loop` still build the mode with `_replace(..., artifact_subdir=_artifact_subdir(relpath))`.
- **Rules** — WARN (non-blocking): there is no `.ai-factory/RULES.md`, so no convention gate applies.
- **Roadmap** — OK. The plan matches contract line 25.2 in the named roadmap `trickster77777.md`, which is the next unchecked task after 25.1.2 `[x]`. Plans route to `plans/trickster77777/`, as they should for a named roadmap. The plan covers the contract line and its spec clause by clause: the function, `process_task`, `_run_dynamic_loop` and its callers, the test, and behaviour neutrality. The plan cites the spec and its governing spec by heading name, not by position.
- **Skill context** — none present (`.ai-factory/skill-context/` absent).

### Verification against the codebase

I checked every claim in the plan against `orchestrator/main.py` and `tests/test_main.py` as they stand now:

- `Mode` is defined at the top of `main.py`, and `artifact_subdir: str | None = None` is on it. `_artifact_subdir` comes after it, so placing `_artifact_dir` right after `_artifact_subdir` is valid. The module also has `from __future__ import annotations`, so the annotation would resolve anyway.
- `process_task` builds `ai_factory`, `plans_dir`, `output_dir` (`mode.verify.output_dirname`) and `plan_reviews_dir`, then joins `mode.artifact_subdir` under `if mode.artifact_subdir:`, then calls the three `mkdir`s. `ai_factory` has no other use: `roadmap_path` rebuilds `project_dir / ".ai-factory"` itself. Removing it is safe, and leaving `roadmap_path` alone is correct.
- `_run_dynamic_loop` has signature `(project_dir, roadmap_path, config, process_fn, artifact_subdir: str | None = None)`. It joins and calls `mkdir` on the plans directory before parsing the roadmap, and reads that directory only through `_next_number(plans_dir)`. Keeping the `mkdir` in place keeps directory creation behaviour the same, including the early "All tasks are done!" return.
- `_test_loop` and `_implement_loop` are the only callers, and both pass `artifact_subdir=mode.artifact_subdir` as a keyword. `notify.py` mentions `_run_dynamic_loop` only in comments. No test or doc references the parameter, so the signature change has no hidden consumers.
- `TEST_RUN_VERIFY.output_dirname == "test-runs"` and `REVIEW_VERIFY.output_dirname == "reviews"` (`agents.py`). `IMPLEMENT_MODE` and `TEST_MODE` both have `artifact_subdir=None`, so the "no subdirectory" case can use them directly.
- In `tests/test_main.py`, the `from orchestrator.main import (...)` block is alphabetised. `_artifact_dir` sorts before `_artifact_subdir`, and the uppercase constants sort before the underscored names under ASCII order. The `_artifact_subdir` tests use the `# ---` banner and "Should …" docstring style, and the next section (the `_detect_task_step` subdir test) follows them. So "a section after the `_artifact_subdir` tests" is a well-defined insertion point.
- The test cases match the spec's test clause exactly (flat → `.ai-factory/plans`, `john-doe` → `.ai-factory/plans/john-doe`, `TEST_MODE.verify.output_dirname` → `.ai-factory/test-runs`). Asserting against the literal `"test-runs"` catches a changed dirname, which is the silent failure the spec names.

### Critical Issues

None.

### Positive Notes

- Making `mode` a required parameter with no default on `_run_dynamic_loop` removes the old `None` default. That default let a caller silently get the flat layout, which was the exact failure the spec describes.
- The plan says explicitly that `_artifact_dir` is pure and creates no directory. This keeps the "behaviour-neutral, including when directories get created" clause testable and stops the derivation from picking up a side effect.
- It uses the same truthiness test (`if mode.artifact_subdir:`) as today, so an empty-string subdirectory behaves the same as before.
- The plan keeps scope tight: `_artifact_subdir` and its tests are left alone, `roadmap_path` is correctly excluded as not an artifact directory, and no docs change is needed because no doc describes the internal parameter.

PLAN_REVIEW_PASS
