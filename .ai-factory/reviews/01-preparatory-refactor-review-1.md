# Review: Preparatory refactor

## Files changed
- `orchestrator/agents.py` — added `PipelineStopError` exception class
- `orchestrator/main.py` — removed `MAX_REVIEW_ITERATIONS` global, added env-var-driven config, threaded `max_review_iterations` parameter, added `PipelineStopError` handler

## Parameter threading verification

Every function that previously read `MAX_REVIEW_ITERATIONS` now accepts `max_review_iterations: int = 3` and all call sites pass it through:

| Caller | Callee | Passes param? |
|--------|--------|---------------|
| `cli()` | `run_implement(project_dir, max_review)` | Yes |
| `cli()` | `run_implement_review(project_dir, max_review)` | Yes |
| `cli()` | `run_review(project_dir, max_review)` | Yes |
| `run_implement()` | `_implement_loop(project_dir, max_review_iterations)` | Yes |
| `run_implement_review()` closure | `_implement_loop(project_dir, max_review_iterations)` | Yes |
| `run_implement_review()` closure | `run_review(project_dir, max_review_iterations)` | Yes |
| `_implement_loop()` | `process_milestone(..., max_review_iterations)` | Yes |
| `run_review()` closure | `review_plan(project_dir, plan_path, max_review_iterations)` | Yes |

Both internal usage sites in `process_milestone` (lines 116, 133-134) and `review_plan` (lines 163, 175-176) use the parameter — no stale references to the deleted global remain.

## Exception handling

`PipelineStopError` is caught in `cli()` at line 371, before `RateLimitError` at line 376. Neither is a subclass of the other, so ordering is irrelevant — both exit cleanly with `sys.exit(0)`. The exception propagates correctly through `_with_caffeinate` (which re-raises after printing elapsed time).

## Observations (non-critical)

1. **`max_refactor` unused** — read at line 356 but not referenced elsewhere. Intentional per plan (placeholder for next milestone). A linter would flag it, but no linter is configured.
2. **Invalid env var values** — `int(os.environ.get(...))` at lines 355-356 will raise `ValueError` on non-integer input. Standard Python behavior; not worth adding validation for an internal tool.
3. **Stale docs** — `CLAUDE.md` and `DESCRIPTION.md` still reference `MAX_REVIEW_ITERATIONS = 3 in main.py`. Not in scope for this milestone but worth updating separately.

## Verdict

Clean, mechanical refactor. All references updated, parameter threading is complete with no gaps, exception handling follows existing patterns. No bugs, no runtime issues.

REVIEW_PASS
