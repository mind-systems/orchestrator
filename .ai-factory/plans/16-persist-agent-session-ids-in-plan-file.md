# Plan: Persist agent session IDs in plan file

## Context
`PlannerReviewer` and `Implementer` hold their Claude session IDs only in memory. On crash/restart the orchestrator resumes the correct milestone step but loses session continuity, so the planner-context-sharing reviewer and the mid-fix implementer both start fresh. Persist the session IDs in an HTML comment block at the end of the plan file and reload them on resume.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Helpers and persistence in agents.py

- [x] **Task 1: Add `re` import and session helpers to `agents.py`**
  Files: `orchestrator/agents.py`
  Add `import re` to the top-level imports (after the existing `import` block, before `from pathlib import Path` if needed, keeping import groups tidy). Below the existing module-level constants (`MAX_RETRIES`, `RETRY_DELAY`), add the compiled regex and two helpers exactly as specified in `.ai-factory/notes/03-session-id-persistence.md`:
  - `_SESSIONS_RE = re.compile(r'<!-- orchestrator-sessions\n(.*?)\n-->', re.DOTALL)`
  - `def _read_sessions(plan_path: Path) -> dict[str, str]` — returns `{}` when the plan file doesn't exist or the block is absent; otherwise parses `key: value` lines.
  - `def _write_session(plan_path: Path, role: str, session_id: str) -> None` — no-op if the plan file doesn't exist or `session_id` is empty; updates the existing block in place if present, appending the role line if missing; otherwise appends a fresh block with a leading blank line and trailing newline.
  Match the implementations from the notes verbatim (function bodies, regex, format).

- [x] **Task 2: Persist planner session after each `_run_claude` in `PlannerReviewer`** (depends on Task 1)
  Files: `orchestrator/agents.py`
  In `PlannerReviewer.plan()` (around line 205) and `PlannerReviewer.review()` (around line 227), add `_write_session(plan_path, "planner", self.session_id)` immediately after the `_run_claude(...)` call that assigns `self.session_id`. Do not modify `PlannerReviewer.patch()` — `patch()` writes to `patch_path`, not the plan, and is unused in the implement/test flows where this persistence matters.

- [x] **Task 3: Persist implementer session after `_run_claude` in `Implementer.implement()`** (depends on Task 1)
  Files: `orchestrator/agents.py`
  In `Implementer.implement()` (around line 343), add `_write_session(plan_path, "implementer", self.session_id)` immediately after the `_run_claude(...)` call. `plan_path` is already a parameter of the method.

### Phase 2: Restore sessions in main.py

- [x] **Task 4: Import `_read_sessions` in `main.py`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Update the existing import on line 13 to also pull in `_read_sessions`:
  `from .agents import Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, RateLimitError, RefactorPlanner, TestRunner, _read_sessions`

- [x] **Task 5: Restore sessions in `process_milestone()`** (depends on Task 4)
  Files: `orchestrator/main.py`
  In `process_milestone()`, after the `planner_reviewer` and `implementer` are constructed (immediately after line 167, i.e. after `implementer = Implementer(project_dir)`) and where `plan_path` is already the canonical one returned by `_detect_milestone_step()`, add:
  ```python
  if plan_path.exists():
      sessions = _read_sessions(plan_path)
      planner_reviewer.session_id = sessions.get("planner")
      implementer.session_id = sessions.get("implementer")
  ```
  This must run *before* the `if step == "plan":` block so a revised plan attempt re-uses the saved planner session.

- [x] **Task 6: Restore sessions in `process_test_milestone()`** (depends on Task 4)
  Files: `orchestrator/main.py`
  In `process_test_milestone()`, after `test_runner = TestRunner()` (around line 548) and before `if step == "plan":`, add the same restoration block as in Task 5:
  ```python
  if plan_path.exists():
      sessions = _read_sessions(plan_path)
      planner_reviewer.session_id = sessions.get("planner")
      implementer.session_id = sessions.get("implementer")
  ```
  Do **not** add this to `process_refactor_milestone()` — refactor flow is explicitly out of scope per the milestone spec and the notes.
