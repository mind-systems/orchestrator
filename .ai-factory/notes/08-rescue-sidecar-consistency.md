# Rescue-Induced Sidecar Inconsistency — Fix

## Problem

After `milestone-rescue` deletes artifacts and updates the plan, the JSON sidecar (`plans/{slug}.json`) retains the old `step` value which may reference files that no longer exist.

Concrete example: plan 21 after rescue has `step: plan_review_failed:2` in the sidecar, but `plan-review-2.md` was deleted. On the next orchestrator run, `_detect_milestone_step` reads `step` → returns `("plan", 3, plan_path)` → `process_milestone` constructs `prev_plan_review = plan-reviews/{seq}-{slug}-plan-review-2.md` and passes it to `planner_reviewer.plan(..., plan_review_path=prev_plan_review)` → the planner tries to read a non-existent file.

## Solution: Validate `step` against disk before trusting it

In `_detect_milestone_step()` in `main.py`, after reading `step_value` from the sidecar and before the early-return dispatch, add a validation step: check whether the artifact the step references actually exists. If it doesn't, clear `step_value` so execution falls through to the heuristic block.

### Validation rules per `step` value

| `step` value | Referenced artifact | Exists check |
|---|---|---|
| `"planned"` | none | always valid |
| `"plan_review_failed:N"` | `plan-reviews/{seq}-{slug}-plan-review-N.md` | must exist |
| `"plan_reviewed"` | last plan-review file ending with `PLAN_REVIEW_PASS` | at least one plan-review with PASS must exist |
| `"implemented"` | none (git tree state checked by heuristic) | always valid |
| `"review_failed:N"` | `reviews/{seq}-{slug}-review-N.md` | must exist |

If the check fails → set `step_value = ""` → falls through to heuristic block.

Same validation in `_detect_test_milestone_step()` for `test_run_failed:N` referencing `test-runs/{seq}-{slug}-test-N.txt`.

### Implementation location

`orchestrator/main.py` — `_detect_milestone_step()` and `_detect_test_milestone_step()`.

No changes to agents, sidecar format, or rescue skill.

## Why not fix in milestone-rescue instead?

The rescue skill is a separate slash-command in a separate project. Fixing it requires updating the skill file AND coordinating the format. Validating in the orchestrator is more robust: it catches any inconsistency regardless of source (rescue, manual edit, out-of-band deletion). Both can coexist — rescue can be updated separately to also write the correct `step` after cleanup.

## Scope

- `orchestrator/main.py`: two functions (`_detect_milestone_step`, `_detect_test_milestone_step`), validation block only — ~10 lines each
- No other files
