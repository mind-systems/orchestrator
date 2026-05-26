# Plan: Persist elapsed time in plan file across resume

## Context
On every restart `milestone_start = time.monotonic()` resets to zero, so the elapsed time written to `ROADMAP.md` after `mark_done()` only reflects the final run segment. Fix by checkpointing the running total as an `elapsed` key inside the existing `<!-- orchestrator-sessions -->` block (no format change — `_write_session` / `_read_sessions` are key-agnostic) and biasing `milestone_start` backward on resume.

The bug exists identically in all three milestone pipelines — `process_milestone`, `process_test_milestone`, and `process_refactor_milestone` — and the fix is the same in each: read `elapsed` once after `_detect_milestone_step` resolves `plan_path`, subtract it from `milestone_start`, and write the running total after every completed step.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: process_milestone

- [x] **Task 1: Read elapsed offset and bias `milestone_start` in `process_milestone()`**
  Files: `orchestrator/main.py`
  In `process_milestone()` (around lines 150–172): after `_detect_milestone_step()` returns and `plan_path` is resolved, but **before** the `if step == "done":` branch at line 157, check whether `plan_path.exists()` and if so call `_read_sessions(plan_path)` once. Compute `elapsed_offset = int(sessions.get("elapsed", "0"))` and reassign `milestone_start = time.monotonic() - elapsed_offset` so subsequent `time.monotonic() - milestone_start` reads include the prior accumulated total. Remove the now-redundant second `_read_sessions(plan_path)` call at line 170 by reusing the `sessions` dict already read (still gate the `planner_reviewer.session_id` / `implementer.session_id` assignments on `plan_path.exists()`). Drop the original `milestone_start = time.monotonic()` at line 150 (the bias path always reinitializes it; keep a single `milestone_start = time.monotonic() - elapsed_offset` assignment in the new location to avoid a dead first call). Import `_write_session` alongside the existing `_read_sessions` import on line 13 — it will be needed by Task 2.

- [x] **Task 2: Checkpoint elapsed total after every completed step in `process_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Add `_write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))` at each of these points in `process_milestone()`:
  1. End of the plan block — right after the `step = "plan_review"` assignment (~line 188), but only when `plan_path.exists()` (guard against the skipped-milestone early return path at line 184–186).
  2. End of each plan-review attempt inside the `for attempt in range(counter, max_iterations + 1):` loop (~lines 192–212) — write after `plan_reviewer.review_plan(...)` returns, both on pass and on the revise-and-continue path. Place the write immediately after the `plan_passed = ...` line so it covers both branches.
  3. End of each implement call — immediately after `implementer.implement(...)` at ~line 229.
  4. End of each review call — immediately after `passed = planner_reviewer.review(...)` at ~line 234.
  Keep the existing `elapsed = int(time.monotonic() - milestone_start)` computation passed to `mark_done()` at line 248 unchanged — it now correctly reflects cumulative time. Same for the `step == "done"` branch at line 158.

### Phase 2: process_test_milestone

- [x] **Task 3: Read elapsed offset and bias `milestone_start` in `process_test_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Mirror Task 1 inside `process_test_milestone()` (around lines 536–558): after `_detect_test_milestone_step()` resolves `plan_path`, and before the `if step == "done":` branch at line 543, read sessions once via `_read_sessions(plan_path)` (guarded by `plan_path.exists()`), compute `elapsed_offset = int(sessions.get("elapsed", "0"))`, and reassign `milestone_start = time.monotonic() - elapsed_offset`. Drop the original `milestone_start = time.monotonic()` at line 536 (single assignment in the new location). Reuse the `sessions` dict for the existing planner/implementer session-id assignments at lines 555–558 instead of reading a second time.

- [x] **Task 4: Checkpoint elapsed total after every completed step in `process_test_milestone()`** (depends on Task 3)
  Files: `orchestrator/main.py`
  Add `_write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))` at each of these points in `process_test_milestone()`:
  1. End of the plan block — after `step = "plan_review"` (~line 574), guarded so the skipped-milestone early return at line 569–572 does not write.
  2. End of each plan-review attempt inside the `for attempt in range(counter, max_iterations + 1):` loop (~lines 578–598) — after `plan_passed = plan_reviewer.review_plan(...)`, covering both pass and revise branches.
  3. End of each implement call — immediately after `implementer.implement(...)` at ~line 613.
  4. End of each test run — immediately after `passed = test_runner.run(...)` at ~line 618.
  The existing `elapsed = int(time.monotonic() - milestone_start)` at line 635 and inside the `step == "done"` branch at line 544 now naturally reflect cumulative time and need no other change.

### Phase 3: process_refactor_milestone

- [x] **Task 5: Read elapsed offset and bias `milestone_start` in `process_refactor_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Mirror Task 1 inside `process_refactor_milestone()` (around lines 275–292): after `_detect_milestone_step()` resolves `plan_path`, and before the `if step == "done":` branch at line 282, read sessions once via `_read_sessions(plan_path)` (guarded by `plan_path.exists()`), compute `elapsed_offset = int(sessions.get("elapsed", "0"))`, and reassign `milestone_start = time.monotonic() - elapsed_offset`. Drop the original `milestone_start = time.monotonic()` at line 275 (single assignment in the new location). Note that `process_refactor_milestone` does not currently restore session IDs from the plan file (`refactor_planner` and `implementer` are created at lines 291–292 without reading sessions); do not introduce that here — out of scope. Only the elapsed offset matters for this task.

- [x] **Task 6: Checkpoint elapsed total after every completed step in `process_refactor_milestone()`** (depends on Task 5)
  Files: `orchestrator/main.py`
  Add `_write_session(plan_path, "elapsed", str(int(time.monotonic() - milestone_start)))` at each of these points in `process_refactor_milestone()`:
  1. End of the audit + plan block — right after the `step = "plan_review"` assignment (~line 308), guarded by `plan_path.exists()` to avoid the skipped-milestone early-return path at lines 303–306.
  2. End of each plan-review attempt inside the `for attempt in range(counter, max_iterations + 1):` loop (~lines 312–332) — after `plan_passed = plan_reviewer.review_plan(...)` (~line 316), covering both pass and revise branches.
  3. End of each implement call — immediately after `implementer.implement(...)` at ~line 349.
  4. End of each verify call — immediately after `passed = refactor_planner.verify(...)` at ~line 355.
  The existing `elapsed = int(time.monotonic() - milestone_start)` at line 371 and inside the `step == "done"` branch at line 283 now naturally reflect cumulative time and need no other change.

<!-- orchestrator-sessions
planner: e68a635e-6898-4ebb-99b0-61d7e89d9cd9
implementer: 24688522-2761-4799-bdc0-6ed854b82949
-->
