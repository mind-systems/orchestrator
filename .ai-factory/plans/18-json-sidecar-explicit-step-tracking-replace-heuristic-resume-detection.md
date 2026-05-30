# Plan: JSON sidecar + explicit step tracking — replace heuristic resume detection

## Context
Move orchestrator session/step state out of the `<!-- orchestrator-sessions -->` HTML comment in plan markdown into a sibling `{slug}.json` sidecar file, and record the completed pipeline step explicitly after each phase so that `_detect_milestone_step()` resumes from a known state instead of guessing from `git diff` + file globs. Fixes the case where an interrupted `implement` (dirty tree, no review file) was incorrectly resumed as `review`. Spec: `.ai-factory/notes/04-explicit-step-tracking.md`.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Sidecar storage in `agents.py`

- [x] **Task 1: Replace HTML comment state with JSON sidecar in `orchestrator/agents.py`**
  Files: `orchestrator/agents.py`
  Delete the `_SESSIONS_RE` regex (line 25). Replace `_read_sessions(plan_path: Path) -> dict[str, str]` and `_write_session(plan_path: Path, key: str, value: str) -> None` with the sidecar versions from `.ai-factory/notes/04-explicit-step-tracking.md` §1. Sidecar path is `plan_path.with_suffix('.json')`. `_read_sessions` returns `{}` when the sidecar does not exist. `_write_session` reads the sidecar (or `{}`), sets `data[key] = value`, writes back with `json.dumps(data, indent=2)`. Keep the existing parameter name `key` (rename from current `role`) and `value` (rename from current `session_id`) for clarity — the same function now stores `planner`, `implementer`, `elapsed`, and the new `step` keys. `import json` is already present (line 6) — no new imports needed. Do NOT keep any backward-compat fallback to the HTML comment.

### Phase 2: Explicit step tracking in `main.py`

- [x] **Task 2: Write `step` after each phase in `process_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  In `process_milestone()` (lines 131–262), add `_write_session(plan_path, "step", "<value>")` calls per spec §2 table:
  - After `planner_reviewer.plan(...)` succeeds and `plan_path.exists()` (around line 194, alongside the existing `elapsed` write) → `"planned"`.
  - Inside the plan-review loop, when `plan_passed` is False AND we will iterate again (i.e. before `planner_reviewer.plan(..., plan_review_path=...)` at line 216) → `"plan_review_failed:{attempt}"`. When `plan_passed` is True (after `break` at line 207) → `"plan_reviewed"`.
  - After `implementer.implement(...)` returns (around line 237, alongside the existing `elapsed` write) → `"implemented"`.
  - In the implement/review loop when review fails and we will iterate again (after the `else` at line 248, before continuing the loop) → `"review_failed:{iteration}"`.
  Place the `step` write right next to the existing `elapsed` write so the two stay in sync. Keep all existing `elapsed` and session-id writes unchanged.

- [x] **Task 3: Read `step` first in `_detect_milestone_step()`** (depends on Task 2)
  Files: `orchestrator/main.py`
  In `_detect_milestone_step()` (lines 63–128), after the canonical-seq resolution block (lines 77–91) and the "plan doesn't exist" early return (lines 94–95), import/reference `_read_sessions` (already imported on line 13) and read `sessions = _read_sessions(plan_path)`, then `step_value = sessions.get("step", "")`. If `step_value` is non-empty, map it per spec §2 table and return early:
  - `"planned"` → `("plan_review", 1, plan_path)`
  - `"plan_review_failed:N"` → `("plan", int(N) + 1, plan_path)`
  - `"plan_reviewed"` → `("implement", 1, plan_path)`
  - `"implemented"` → `("review", 1, plan_path)`
  - `"review_failed:N"` → `("implement", int(N) + 1, plan_path)`
  If `step_value` is empty or unrecognized, fall through to the existing heuristic block (lines 97–128) untouched — this covers old plans that have no sidecar (refactor-mode plans rely on this fallback too).

- [x] **Task 4: Write `step` after each phase in `process_test_milestone()`** (depends on Task 1)
  Files: `orchestrator/main.py`
  Mirror Task 2 inside `process_test_milestone()` (lines 536–666):
  - After successful plan (around line 597) → `"planned"`.
  - In the plan-review loop, on fail-before-retry → `"plan_review_failed:{attempt}"`; on pass → `"plan_reviewed"`.
  - After `implementer.implement(...)` (around line 638) → `"implemented"`.
  - In the implement/test-run loop, when `passed` is False and we iterate again (after line 649) → `"test_run_failed:{iteration}"` (NOT `review_failed` — this is the test variant).

- [x] **Task 5: Read `step` first in `_detect_test_milestone_step()`** (depends on Task 4)
  Files: `orchestrator/main.py`
  Mirror Task 3 inside `_detect_test_milestone_step()` (lines 484–533). Mapping table is the same except:
  - `"implemented"` → `("test_run", 1, plan_path)`
  - `"test_run_failed:N"` → `("implement", int(N) + 1, plan_path)`
  Fall through to the existing heuristic (lines 505–533) when `step` is absent/unrecognized.

## Commit Plan
- **Commit 1** (after Task 1): "Replace orchestrator-sessions HTML comment with JSON sidecar"
- **Commit 2** (after Tasks 2–3): "Track milestone step explicitly in implement pipeline"
- **Commit 3** (after Tasks 4–5): "Track milestone step explicitly in test pipeline"

<!-- orchestrator-sessions
planner: 4b0a8275-7fcb-408e-90ce-c958adfd8101
elapsed: 775
implementer: bfc7e4c4-e653-4101-87da-7cf58492a5cc
-->
