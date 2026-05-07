# Plan: Log session_id on new session start

## Context
Print the session_id to the orchestrator log after the first `_run_claude()` call that creates a new session for each agent, making it easy to trace which Claude session backs each agent.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Add session_id logging

- [x] **Task 1: Log session_id in PlannerReviewer.plan()**
  Files: `orchestrator/agents.py`
  In `PlannerReviewer.plan()` (around line 185): capture whether `self.session_id` was `None` before the `_run_claude()` call. After the call assigns `self.session_id`, if it was previously `None`, print `f"  [session: {self.session_id}]"`. Pattern: save a flag like `is_new = self.session_id is None` before the call, then `if is_new: print(...)` after.

- [x] **Task 2: Log session_id in PlanReviewer.review_plan()**
  Files: `orchestrator/agents.py`
  In `PlanReviewer.review_plan()` (around line 269): this agent has no persistent `session_id` — every call is a fresh session. Capture the returned session_id from `_run_claude()` (currently the return value is discarded) and print `f"  [session: {sid}]"` unconditionally after the call.

- [x] **Task 3: Log session_id in Implementer.implement()**
  Files: `orchestrator/agents.py`
  In `Implementer.implement()` (around line 323): same pattern as Task 1. Save `is_new = self.session_id is None` before the `_run_claude()` call, then `if is_new: print(f"  [session: {self.session_id}]")` after.

- [x] **Task 4: Log session_id in RefactorPlanner.audit_and_plan()**
  Files: `orchestrator/agents.py`
  In `RefactorPlanner.audit_and_plan()` (around line 370): same pattern as Task 1. Save `is_new = self.session_id is None` before the `_run_claude()` call, then `if is_new: print(f"  [session: {self.session_id}]")` after.
