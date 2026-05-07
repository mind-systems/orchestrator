# Plan: Fix seq mismatch in resume detection

## Context
When a previous run is interrupted after writing a plan file, the next run computes a new (higher) seq via `_next_number()`, causing `_detect_milestone_step()` to look for artifacts under the wrong seq prefix and fall back to `step="plan"` — losing all existing progress.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Fix `_detect_milestone_step()` to resolve canonical seq from slug

- [x] **Task 1: Add slug-based scan and canonical seq resolution inside `_detect_milestone_step()`**
  Files: `orchestrator/main.py`
  At the top of `_detect_milestone_step()`, before the `plan_path.exists()` check:
  1. Glob `plans_dir` (derive from `plan_path.parent`) for `*-{slug}.md`.
  2. If matches are found, extract the numeric prefix from each match's filename (split on `-`, take first part if digit).
  3. Pick the match with the lowest numeric prefix — that's the canonical file from the original run.
  4. Derive `canonical_seq` from that file's prefix and `canonical_plan_path` from that file's full path.
  5. Override the local `seq` and `plan_path` with canonical values for all subsequent lookups within this function (plan-reviews glob, reviews glob).
  6. If no matches are found, proceed as before — use the passed `seq` and `plan_path` unchanged.

- [x] **Task 2: Change return type to include canonical `plan_path`**
  Files: `orchestrator/main.py`
  Change `_detect_milestone_step()` return type from `tuple[str, int]` to `tuple[str, int, Path]`. The third element is the canonical `plan_path` (either the discovered original or the passed one if no slug match was found). Update the docstring.

### Phase 2: Update callers to use the returned canonical path and seq

- [x] **Task 3: Update `process_milestone()` to use returned canonical plan_path and derive seq from it** (depends on Task 2)
  Files: `orchestrator/main.py`
  1. Unpack the third return value: `step, counter, plan_path = _detect_milestone_step(...)` — this reassigns the local `plan_path`.
  2. Derive `seq` from the canonical plan_path's filename: `seq = plan_path.stem.split("-", 1)[0]`.
  3. All subsequent code in the function already uses the local `seq` and `plan_path` variables, so they'll automatically pick up the correct values for plan-review paths, review paths, and agent calls.

- [x] **Task 4: Update `process_refactor_milestone()` to use returned canonical plan_path and derive seq from it** (depends on Task 2)
  Files: `orchestrator/main.py`
  Same change as Task 3 but in `process_refactor_milestone()`:
  1. Unpack: `step, counter, plan_path = _detect_milestone_step(...)`.
  2. Derive: `seq = plan_path.stem.split("-", 1)[0]`.
  3. All downstream uses of `seq` and `plan_path` automatically correct.
