# Plan: 30.1 — a plan reviewer's session id is kept in the sidecar

## Context
`PlanReviewer.review_plan` discards the session id `_run_claude` returns. Keep it in the plan's sidecar under `plan-reviewer-<attempt>` as soon as the reviewer returns, so a rescue can resume that reviewer's session. The governing spec (`docs/features/resume.md` § What the sidecar holds) already states this behavior; only code and tests change. Resume reads sidecar keys by name (`step`, `elapsed`, `escalation`, `planner`, `implementer`), so it ignores the new key and needs no change.

## Settings
- Testing: yes (update the three named tests in `tests/test_agents.py`; no new tests)
- Logging: minimal
- Docs: no (resume.md already describes the target)

## Tasks

### Record the session id

- [x] **`review_plan` takes the attempt and writes the session id**
  Files: `orchestrator/agents.py`
  In `PlanReviewer.review_plan`, change the signature to `review_plan(self, plan_path: Path, review_path: Path, attempt: int) -> bool`. Right after the `_, sid = _run_claude(...)` call returns, before the `if not review_path.exists():` check, add `_write_session(plan_path, f"plan-reviewer-{attempt}", sid)`. That way a reviewer that wrote no review (the `MissingArtifactError` path) or that escalated still leaves its id. `_write_session` overwrites an existing key, so an attempt that runs again on resume replaces its own key. Keep everything else as it is: the escalation path still writes only `escalation` and `step`, the non-escalation path writes no `step`, and the return value stays `_has_signal(review_text, "PLAN_REVIEW_PASS")`. Update the docstring: it should say the session id is written to the sidecar under `plan-reviewer-<attempt>` before the review file is checked. Per the global rules, it must not cite the roadmap or the plan.

- [x] **`process_task` passes the attempt** (depends on the `review_plan` change)
  Files: `orchestrator/main.py`
  In the plan-review loop in `process_task` (`for attempt in range(counter, max_iterations + 1):`), change the call to `plan_reviewer.review_plan(plan_path, plan_review_path, attempt)`. `attempt` is the same number that goes into the `-plan-review-<attempt>.md` artifact name, so the key and the artifact match. There are no other callers (checked with grep across `orchestrator/` and `tests/`).

### Pin it in tests

- [x] **Update the three `review_plan` tests** (depends on the `review_plan` change)
  Files: `tests/test_agents.py`
  - `test_review_plan_regression_no_escalation_returns_bool`: call `reviewer.review_plan(plan_path, review_path, 1)`. Replace `assert not plan_path.with_suffix(".json").exists()` with `assert json.loads(plan_path.with_suffix(".json").read_text()) == {"plan-reviewer-1": "sid-1"}`. `sid-1` is the id `_stub_run_claude_writing` returns. Update the docstring: it currently says no sidecar is written. It should say the sidecar holds only the reviewer's session id, with no `step` and no `escalation`.
  - `test_review_plan_missing_file_raises_missing_artifact_error`: call `reviewer.review_plan(plan_path, review_path, 1)` inside the `pytest.raises` block. Keep the two message-line assertions. Replace the no-sidecar assertion with `assert json.loads(plan_path.with_suffix(".json").read_text()) == {"plan-reviewer-1": "sid-1"}`. Update the docstring: the session id is written even though no review exists, and no `step` is written.
  - `test_review_plan_escalation_raises_and_writes_sidecar`: call `reviewer.review_plan(plan_path, review_path, 1)`. Keep the existing `step == "escalated"` and `escalation` assertions.
  Run `uv run pytest` and confirm the whole suite passes.
