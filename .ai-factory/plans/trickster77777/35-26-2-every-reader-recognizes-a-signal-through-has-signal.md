# Plan: 26.2 — every reader recognizes a signal through `_has_signal`

## Context
The live reviews (`PlannerReviewer.review`, `PlanReviewer.review_plan`) recognize a completion signal through `_has_signal` in `orchestrator/protocol.py`, which looks for an exact line among the last five lines. Three other readers still use `.read_text().strip().endswith(...)`: `process_task`'s plan-review safety guard in `pipeline.py`, and `_validate_sidecar_step` and `_detect_step` in `resume.py`. So a passing review with a stray line after its signal is accepted live, then stops the run at the guard or is misread on resume. This task routes those readers through `_has_signal`, fixes `_validate_sidecar_step`'s docstring, and adds two `_detect_step` regression tests. Spec: `.ai-factory/specs/trickster77777/0076-every-reader-recognizes-a-signal-one-way.md`. Governing spec: `docs/pipeline.md` § Completion signals. That section already states the last-five-lines reading, so no doc changes.

## Settings
- Testing: yes (the two tests the spec names, nothing more)
- Logging: minimal
- Docs: no

## Tasks

### Route the readers through `_has_signal`

- [x] **`pipeline.py`: the plan-review guard reads through `_has_signal`**
  Files: `orchestrator/pipeline.py`
  Extend `from .protocol import PLAN_REVIEW_PASS, _read_sessions, _write_session` to `from .protocol import PLAN_REVIEW_PASS, _has_signal, _read_sessions, _write_session`, keeping alphabetical order with uppercase first. In `process_task`, find the block under the comment `# Safety guard: ensure a passing plan review exists before implementing`. Change its condition from `not _plan_review_files[-1].read_text().strip().endswith(PLAN_REVIEW_PASS)` to `not _has_signal(_plan_review_files[-1].read_text(), PLAN_REVIEW_PASS)`. Keep the `not _plan_review_files or ...` short-circuit, the `PipelineStopError` and its message as they are.

- [x] **`resume.py`: `_validate_sidecar_step` and `_detect_step` read through `_has_signal`**
  Files: `orchestrator/resume.py`
  Extend `from .protocol import PLAN_REVIEW_PASS, _read_sessions` to `from .protocol import PLAN_REVIEW_PASS, _has_signal, _read_sessions`. `resume` still imports only from `ports` and `protocol`. Then make three check changes, each on the file's full `read_text()` with no `.strip()`, since `_has_signal` strips each line itself:
  - `_validate_sidecar_step`, `plan_reviewed` branch: `f.read_text().strip().endswith(PLAN_REVIEW_PASS)` inside the `any(...)` becomes `_has_signal(f.read_text(), PLAN_REVIEW_PASS)`.
  - `_detect_step`, step 4 (comment `# 4. Latest plan-review didn't pass → plan needs revision`): `not plan_review_files[-1].read_text().strip().endswith(PLAN_REVIEW_PASS)` becomes `not _has_signal(plan_review_files[-1].read_text(), PLAN_REVIEW_PASS)`.
  - `_detect_step`, step 7 (comment `# 7. Latest verify-output passed → ...`): `output_files[-1].read_text().strip().endswith(verify.pass_signal)` becomes `_has_signal(output_files[-1].read_text(), verify.pass_signal)`.
  In `_validate_sidecar_step`'s docstring, replace the bullet `- plan_reviewed and no plan-review file ends with PLAN_REVIEW_PASS.` with one that states the last-five-lines reading, e.g. `- plan_reviewed and no plan-review file carries PLAN_REVIEW_PASS as an exact line among its last five lines.` Leave the other docstring bullets and the step comments unchanged. "didn't pass" and "passed" stay true under the new reading.
  After this, `grep -n "endswith" orchestrator/resume.py orchestrator/pipeline.py` returns nothing.

### Regression tests

- [x] **Two `_detect_step` tests with a stray line after the pass signal** (depends on both tasks above)
  Files: `tests/test_main.py`
  Add two tests beside the existing `_detect_step` tests. Use the existing helpers `_dms_dirs`, `_detect_task_step` (which calls `_detect_step` with `REVIEW_VERIFY`) and `_init_dirty_git_repo`, and the constants `DMS_SEQ`/`DMS_SLUG`. Each fixture puts a non-signal stray line after the signal line, e.g. `"Review notes\n\nPLAN_REVIEW_PASS\nstray trailing line\n"`. No new imports are needed.
  - `test_detect_task_step_plan_review_pass_with_stray_line_returns_implement`: place it right after `test_detect_task_step_clean_tree_no_sidecar_passing_plan_review_returns_implement` and mirror that test's setup. Write the plan file, write no sidecar, write plan-review-1 with `PLAN_REVIEW_PASS` followed by a stray line, then run `git init` plus the empty `--allow-empty` commit so the tree is clean. Assert `("implement", 1, plan_path)`. Today this resolves to `("plan", 2, ...)`.
  - `test_detect_task_step_review_pass_with_stray_line_returns_done`: place it right after `test_detect_task_step_dirty_tree_review_passing_returns_done` and mirror that test's setup. Write the plan file, a passing plan-review-1 (signal as its last line, as today), and review-1 with `REVIEW_PASS` followed by a stray line, then call `_init_dirty_git_repo(tmp_path)`. Assert `("done", 0, plan_path)`. Today this resolves to `("implement", 2, ...)`.
  Each docstring states the expected result and why it matters: a resume that misreads a passing artifact silently repeats finished work. Per the spec, the `pipeline` guard gets no test, because it fails loudly with `PipelineStopError`. Do not add `_validate_sidecar_step` tests either.

- [x] **Run the suite** (depends on the tests task)
  Run `uv run pytest`. All tests pass, including every existing resume and pipeline test, whose fixtures end with the signal as their last line and so resolve as before.
