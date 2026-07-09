# Code Review: Express the milestone pipeline once (implement / test)

**Scope:** `orchestrator/main.py` (only code file changed). Reviewed against the pre-refactor behaviour, the spec (`06-unify-milestone-pipeline.md`), and the test suite.

## What changed
`process_milestone` + `process_test_milestone` collapsed into one `process_milestone(..., mode=IMPLEMENT_MODE, phase_session_id=None)`; `_detect_milestone_step` + `_detect_test_milestone_step` collapsed into `_detect_step` with the two original names retained as thin wrappers; a `Mode` `NamedTuple` carries the static divergences and a `_verify` closure carries the two runtime ones.

## Verification performed
- `uv run pytest` — **91 passed**. The detector-matrix safety net stays fully green with no assertion touched.
- Grepped the codebase: no dangling references to `process_test_milestone`; the only `process_milestone` callers are the two loop lambdas (`main.py:593,606`) and the resume-past-max test (`test_main.py:789`, 4-arg call resolving to the `IMPLEMENT_MODE` default).

## Behaviour-preservation audit (byte-for-byte)
- **Parametrized glob** (`_detect_step:293`): `output_suffix.format(n='*')` yields `"-review-*.md"` / `"-test-*.txt"`, reproducing the original `f"{seq}-{slug}-review-*.md"` / `-test-*.txt` patterns exactly.
- **Detector tail equivalence**: implement's `not files→review / not PASS→implement / else done` and test's `not files→test_run / PASS→done / else implement` are the same logic phrased inversely; both collapse cleanly to `not output_files→verify_step / endswith pass_signal→done / else implement(len+1)`. Sidecar dispatch order (`plan_review_failed:` checked before `verify_fail_tag`) is preserved, so `plan_review_failed:N` is never mis-caught by `review_failed:`/`test_run_failed:`.
- **`_validate_sidecar_step`** unchanged; called with `verify_fail_tag` + `output_suffix` matching the originals.
- **Raise-message templates**: `mode.max_iterations_message.format(n=..., path=out_path, content=out_path.read_text())` produces output identical to the original f-strings. Substituted `content` is a value, not a re-parsed template, so review/test-output text containing `{...}` cannot raise `KeyError`/`IndexError` — no format-injection regression.
- **`prev_out_path`**: gated on `mode.verify_step == "review"`, so prev-review re-verification stays implement-only; test mode always passes `None`. `TestRunner()` is constructed only when `verify_step == "test_run"`.
- **Closure captures**: `_verify` closes over the final canonical `plan_path` (last assigned at :346-350, never reassigned afterward), `planner_reviewer`, `test_runner`, `project_dir` — all bound before the closure is defined.
- **Exception split (task 05)** preserved at every collapsed raise site: plan-fail / no-passing-plan-review / verify-fail → `PipelineStopError`; resume-past-max → `HaltError`.
- **Every observable string** — banner (`{mode.header_label}:`), resume print, skip message, `PLANNING`/`REVIEWING PLAN`, verify-running header, pass/fail lines, `Milestone done`, sidecar `step` writes (`planned`/`plan_reviewed`/`implemented`/`review`|`test_run`/`review_failed:N`|`test_run_failed:N`), artifact filenames, feedback paths, and commit/notify calls — matches the pre-refactor literals.
- **`_implement_loop`** uses `IMPLEMENT_MODE._replace(planner_prompt_name=..., roadmap_filename=...)` (valid on a `NamedTuple`), so the implement variant that passes non-default prompt/roadmap still works; the default args reproduce `IMPLEMENT_MODE` unchanged.

## Findings
None. The refactor is a faithful, behaviour-preserving dedup: identical resume dispatch in both modes, identical artifacts/sidecar strings/print lines, and the test suite is green with no assertion weakened.

REVIEW_PASS
