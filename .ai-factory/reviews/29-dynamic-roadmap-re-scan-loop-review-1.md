# Code Review: Dynamic roadmap re-scan loop (review 1)

## Scope
`orchestrator/main.py` — extraction of `_run_dynamic_loop`, conversion of `_implement_loop` / `_test_loop` to thin wrappers. Reviewed against the plan (`29-dynamic-roadmap-re-scan-loop.md`), `roadmap.py`, and the surrounding `process_milestone` / `process_test_milestone` functions.

## Verdict
The implementation is correct and faithful to the plan. No blocking bugs found. Two low-severity, by-design observations are recorded below for the record only — both are explicitly anticipated in the spec note and do not warrant a change.

## Correctness walkthrough

- **Re-scan + top-to-bottom selection**: `parse_roadmap` re-reads the file each iteration and `pending[0]` is selected, so milestones added or reordered mid-run are honored. Correct.
- **Infinite-loop guard**: If `process_fn` returns without flipping the checkbox, the same `(title, description)` is selected next iteration → `signature == last_signature` → `PipelineStopError`. The guard fires on the *second* selection (after `last_signature` was set on the first), which is the intended catch. Consecutive distinct milestones reset `last_signature`, so normal progress is never blocked.
- **`mark_skipped` flips the box too**: `mark_skipped` writes `- [x] ⚠️ SKIPPED …`, which `parse_roadmap` reads as `done=True` (group(1) == "x"). A skipped milestone therefore leaves `pending` on the next scan and does not trip the guard. Correct.
- **`_next_number` per iteration**: After a milestone creates its plan file the count advances; for resumes, `_detect_milestone_step` / `_detect_test_milestone_step` glob `*-{slug}.md` and override the computed seq with the canonical lower-seq file, so a higher `_next_number` value is harmless. Matches the plan's resume reasoning.
- **Stop handling**: `while not state.stop_requested` checks before each milestone (SIGINT lets the current milestone finish), then the post-loop `if state.stop_requested:` prints the halt message. Equivalent to the prior per-iteration check.
- **Lambda closures**: The `process_fn` lambdas capture `project_dir`, `config`, `planner_prompt_name`, `roadmap_filename` — all loop-invariant, so there is no late-binding closure hazard. Return value (`str | None` session id) is threaded back into `phase_session_id` correctly.
- **`---STOP---` / breakpoint**: Unchanged; `parse_roadmap` excludes post-marker milestones from `pending`, and the startup summary reproduces the prior wording.

## Non-blocking observations (no action required)

1. **Duplicate `(title, description)` milestones would trigger a false-positive stop.** If the roadmap legitimately contains two distinct milestones with identical title *and* description, the second is selected immediately after the first is marked done and shares the prior signature, raising `PipelineStopError`. This exact tradeoff is acknowledged in the spec note ("re-selecting a genuinely new task with a coincidentally identical title only triggers after that task failed to flip"). Duplicate entries are an unusual roadmap state; accepting the false stop is the documented design choice. No change needed.

2. **Skipped milestones no longer advance the sequence prefix.** When a milestone is skipped before any plan file is written, `_next_number` returns the same value on the next iteration, so the following milestone reuses that seq prefix (e.g. two distinct slugs both at `05-`). Under the old `enumerate(start=…)` numbering each milestone consumed a unique number. This is harmless: all artifacts are namespaced by `{seq}-{slug}` and resume detection globs by slug, so no file collision or resume confusion results. Purely a cosmetic numbering difference.

## Plan compliance
- `_run_dynamic_loop` signature, startup-summary-once, `while` body, guard, section/phase reset, and post-loop halt message all match Task 1.
- Both loops reduced to existence-check + delegation with the specified lambdas; fixed `pending` iteration and duplicated summary removed; `process_*` signatures unchanged; `_run_loop` left in place (Task 2). Compliant.

REVIEW_PASS
