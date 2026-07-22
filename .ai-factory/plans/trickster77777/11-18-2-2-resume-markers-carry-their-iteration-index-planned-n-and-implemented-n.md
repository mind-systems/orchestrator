# Plan: 18.2.2 — Resume markers carry their iteration index — `planned:N` and `implemented:N`

## Context
Give both "artifact produced" sidecar markers their iteration index — `planned:N` / `implemented:N` — symmetric with the existing `*_failed:N` markers, so resume never re-runs a completed step, resets the round budget, or overwrites a verify/plan-review artifact. Clean break: no bare-marker fallback. This turns 18.2.1's grammar tests (`tests/test_main.py`) green via explicit dispatch (not the disk heuristic).

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Ground-truth notes (read before implementing)
- **Governing spec:** `.ai-factory/specs/trickster77777/32-resume-carries-verify-iteration.md` — the full task spec.
- **Governing doc (intended behavior):** `docs/how-it-works.md:25` already describes the target grammar present-tense — "`planned:N` и `implemented:N` пишутся, когда артефакт раунда N готов … resume возобновляет план-ревью/verify на итерации N, не перезапуская планнер/имплементер". This is the invariant the code must uphold: **the marker carries the actual round number N**. No doc change is needed — the doc leads and already matches the target.
- **18.2.1 tests already on disk** (do not re-add or weaken): `tests/test_main.py` — `_detect_task_step` on `planned:{1,2}`→`("plan_review",N)` (lines ~276–299), `implemented:{1,3}`→`("review",N)` (lines ~302–325), `_detect_test_task_step` `implemented:2`→`("test_run",2)` (line ~680), and `_validate_sidecar_step` on `planned:2`/`implemented:2`→valid, `planned:abc`/`implemented:abc`→`""` (lines ~66–87). After this task each must pass through the **explicit** `planned:`/`implemented:` branches, not the fallback heuristic.
- **Herald migration is already applied:** `/Users/max/projects/repo-stats-herald/.ai-factory/plans/34-6-2-coordination-root-seeding.json` already holds `"step": "implemented:3"`. Task 5 is a verify-only guard, not a rewrite.

## Tasks

### Phase 1: Resume dispatch carries the ordinal (`resume.py`)

- [x] **Task 1: Validate `planned:N` / `implemented:N`, drop the bare tuple**
  Files: `orchestrator/resume.py`
  In `_validate_sidecar_step` (`resume.py:11-57`): **remove** the bare always-valid branch `if step_value in ("planned", "implemented"): return step_value` (lines 31-32) — the tuple becomes empty, so delete the check entirely (no bare marker is ever written after this task). **Add** a new branch, placed before the `plan_review_failed:` check, that handles both indexed artifact-produced markers with the same parse-guard shape as the `fail_prefix` branch (lines 48-55) but **no** artifact-existence stat (validity is structural — there is no per-attempt numbered file):
  ```python
  if step_value.startswith("planned:") or step_value.startswith("implemented:"):
      try:
          int(step_value.split(":")[1])
      except (IndexError, ValueError):
          return ""
      return step_value
  ```
  A well-formed `:N` returns as-is; a malformed tail (`planned:abc`) clears the value so dispatch falls to the heuristic. Update the function docstring (lines 20-28): drop the "`planned` and `implemented` … always valid" sentence and state that `planned:N`/`implemented:N` are structurally valid with a parse-guarded ordinal and no artifact reference.

- [x] **Task 2: Dispatch `planned:N`→`("plan_review",N)` and `implemented:N`→`(verify_step,N)`** (depends on Task 1)
  Files: `orchestrator/resume.py`
  In `_detect_step` (`resume.py:121-134`): replace the exact-match branch `if step_value == "planned": return ("plan_review", 1, plan_path)` (lines 122-123) with a prefix branch that parses the ordinal:
  ```python
  if step_value.startswith("planned:"):
      n = int(step_value.split(":")[1])
      return ("plan_review", n, plan_path)
  ```
  Replace `elif step_value == "implemented": return (verify_step, 1, plan_path)` (lines 129-130) with:
  ```python
  elif step_value.startswith("implemented:"):
      n = int(step_value.split(":")[1])
      return (verify_step, n, plan_path)
  ```
  Keep the surrounding branches unchanged — `plan_review_failed:N`→`("plan", n+1)`, `plan_reviewed`→`("implement", 1)`, `verify_fail_tag`→`("implement", n+1)`, and the `# unrecognized → fall through to heuristic` tail. Prefix order is safe: `"planned:"` never prefixes `"plan_review_failed:"` and `"implemented:"` never prefixes `review_failed:`/`test_run_failed:`, and `plan_review_failed:` is still matched by its own earlier branch. This is the sole dispatch site; the thin wrappers `_detect_task_step` (review mode) and `_detect_test_task_step` (test_run mode) inherit it unchanged, so test mode is covered.

### Phase 2: Marker writes carry the ordinal (`main.py`)

- [x] **Task 3: Index every "artifact produced" write; add the post-re-plan marker** (depends on Task 2)
  Files: `orchestrator/main.py`
  Three edits in `process_task`:
  1. **Plan-ready marker** — `main.py:277` `_write_session(plan_path, "step", "planned")` → `_write_session(plan_path, "step", f"planned:{counter}")`.
     **DEVIATION (spec sketch said `f"planned:1"`, ground truth said `{counter}`, done):** the spec's fix-point-3 sketch writes the literal `planned:1`, but this line is also re-hit on resume from `("plan", N+1)` (a crash **inside** the re-plan at lines 302-305, per spec fix-point-4), where `counter = N+1 > 1`. The governing doc (`how-it-works.md:25`) and the spec's own invariant require `planned:N` to name the round about to be reviewed; writing a literal `1` there would make a subsequent crash resume as `("plan_review", 1)` — re-reviewing attempt 1 with the attempt-(N+1) plan, overwriting `plan-review-1.md` and resetting the plan-review budget: the exact bug class this task removes, reintroduced on the plan side. `f"planned:{counter}"` is byte-identical to `planned:1` in the fresh case (`counter == 1`) and correct on resume. No 18.2.1 test pins the literal written here (they pin dispatch/validation only).
  2. **Revised-plan-ready marker** — after the re-plan call (`main.py:302-305`, i.e. as the last statement of the `for attempt` loop body, after the `planner_reviewer.plan(...)` re-plan), add `_write_session(plan_path, "step", f"planned:{attempt + 1}")`. This records "the revised plan for attempt N+1 is on disk — review it, do not re-plan," so a crash during plan-review attempt N+1 resumes as `("plan_review", N+1)`. Leave the `plan_review_failed:{attempt}` write at line 301 in place (it guards the crash-during-re-plan window).
  3. **Implemented marker** — `main.py:329` `_write_session(plan_path, "step", "implemented")` → `_write_session(plan_path, "step", f"implemented:{iteration}")`. This line serves both `review` and `test_run` verify modes, so test mode is covered. Do **not** touch the implement-loop guard (`main.py:322-324`) or the `max_iterations` guard (`main.py:316-320`); with `implemented:N` dispatching to `(verify_step, N)`, `impl_start` becomes N, the guard short-circuits the already-done implement, and `review-N.md` is written fresh with `review-(N-1).md` as prior.

### Phase 3: Keep the suite green and confirm the migration

- [x] **Task 4: Update the one pre-existing bare-`implemented` fixture** (depends on Task 2)
  Files: `tests/test_main.py`
  `test_detect_task_step_subdird_dirs_dispatches_same_as_flat` (around line 1156) seeds `{"step": "implemented"}` (line ~1166) and asserts `("review", 1)`. Under the clean break the bare marker no longer dispatches — it would fall to the heuristic and, with no plan-review files on disk, return `("plan_review", 1)`, breaking the test. Change that fixture value to `"implemented:1"` so it exercises the explicit branch and keeps asserting `("review", 1)`; the test's subdir-dispatch intent is unchanged. Do **not** touch the 18.2.1 grammar tests. The remaining bare-`"planned"` fixtures in adoption/survivor tests (`test_detect_task_step_untracked_plan_is_adopted` ~line 546, `test_detect_task_step_staged_plan_is_adopted` ~569, `test_detect_task_step_survivor_over_lowest` ~596, `test_detect_test_task_step_sidecar_planned_returns_plan_review` ~711) stay as-is: they exercise the git-adoption heuristic and still resolve to their asserted `("plan_review", 1)` via that heuristic — leave them untouched.

- [x] **Task 5: Confirm the one wounded sidecar is migrated** (depends on Task 2)
  Files: `/Users/max/projects/repo-stats-herald/.ai-factory/plans/34-6-2-coordination-root-seeding.json` (target project, not this repo)
  The spec calls for a one-time hand-migration of this sidecar's `"step"` from bare `"implemented"` to `"implemented:3"` (crash during review iteration 3; `review-1.md`/`review-2.md` on disk, neither `REVIEW_PASS`). The file **already** reads `"step": "implemented:3"` — verify it still does and make no change if so. If it is ever found as bare `"implemented"`, set `step` to `"implemented:3"` (touch only the `step` key; leave `planner`, `implementer`, `elapsed` intact). This migration is only valid once this task's `resume.py`/`main.py` changes are in effect.

## Verify
- `uv run pytest` green, including 18.2.1's flipped `:N` cases (`tests/test_agents.py` / `tests/test_main.py`) — and each such case reached through the explicit `planned:`/`implemented:` branch, not the heuristic.
- Reasoning trace, implement side: `step = "implemented:3"` → `_detect_task_step` → `("review", 3)`; `impl_start = 3`, the `iteration == counter` guard short-circuits implement, `review-3.md` written fresh, `review-2.md` read as prior — no re-implement, no overwrite, no budget reset.
- Reasoning trace, plan side: crash during plan-review attempt 2 leaves `step = "planned:2"` → `("plan_review", 2)` → review attempt 2 with no planner run; crash during the re-plan leaves `step = "plan_review_failed:1"` → `("plan", 2)` → re-plan (correct).
- No bare `planned`/`implemented` remains written by `main.py`, no bare-marker branch remains in `resume.py`, and no `planned:N`/`implemented:N` artifact-existence check was added.
