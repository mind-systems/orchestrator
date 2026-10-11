# A plan reviewer's session id is kept in the sidecar

**Date:** 2026-10-11
**Source:** the user's ask relayed by skills 07 on 2026-10-11, from core 130's rescue of 77.6.1 (rescue report 0031): a rescue should be able to resume a reviewer's session and ask what it saw; and the user's go in chat on 2026-10-11

Governing spec: [resume.md](../../../docs/features/resume.md) — § What the sidecar holds.

## What is true now

`PlanReviewer.review_plan(self, plan_path: Path, review_path: Path) -> bool` in `orchestrator/agents.py` runs the reviewer with `_, sid = _run_claude(...)` and never uses `sid`. It writes the sidecar only on escalation, where it sets `escalation` and `step`. It raises `MissingArtifactError` when the review file is absent after the run. The session id reaches only the terminal's `[session: …]` line.

`process_task` in `orchestrator/main.py` builds a fresh `PlanReviewer(project_dir)` for each `attempt` of the plan-review loop and calls `plan_reviewer.review_plan(plan_path, plan_review_path)`.

The code reviewer runs in the planner's session, which `PlannerReviewer.review` already writes back to the sidecar as `planner`; the implementer's session is kept as `implementer`. The run reads its sidecar keys by name (`step`, `elapsed`, `escalation`, `planner`, `implementer`), so a key it does not name is ignored.

In `tests/test_agents.py`, `test_review_plan_regression_no_escalation_returns_bool` and `test_review_plan_missing_file_raises_missing_artifact_error` assert that no sidecar exists after `review_plan`; `test_review_plan_escalation_raises_and_writes_sidecar` calls `review_plan` without an attempt and asserts `step` and `escalation`.

## What must be true after

`review_plan` takes `attempt: int` after `review_path`. Right after `_run_claude` returns, before the review file is checked, it writes `_write_session(plan_path, f"plan-reviewer-{attempt}", sid)`. A reviewer that wrote no review, or that escalated, still leaves its id. A resumed attempt that runs again replaces its key with the new session. `review_plan` writes no `step` beyond what escalation already writes.

`process_task` passes `attempt` to `review_plan`.

Tests: `test_review_plan_regression_no_escalation_returns_bool` and `test_review_plan_missing_file_raises_missing_artifact_error` assert that the sidecar holds exactly `{"plan-reviewer-1": "sid-1"}`, the id their stub returns, in place of no sidecar. `test_review_plan_escalation_raises_and_writes_sidecar` passes the attempt too. A key missing, or written under the wrong attempt number, fails nothing at run time, which is why the tests pin it.

## What breaks on contact

- Every `review_plan` call takes the third argument: `process_task` and the tests named above.
- The run reads its sidecar keys by name (`step`, `elapsed`, `escalation`, `planner`, `implementer`) and ignores the new key, so a resumed run behaves as before.
- The skills' `orchestrator-artifacts` mirror of the sidecar fields lags until it is told; that is the skills side's.
