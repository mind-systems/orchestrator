# Plan: 24.2 — A review that was never written is a halt, not a failed review

## Context
`PlanReviewer.review_plan` and `PlannerReviewer.review` in `orchestrator/agents.py` return `False` when the reviewer ends its turn without writing its review file, so a machine fault is read as a failed-review verdict. Per the task spec (`.ai-factory/specs/trickster77777/0058-a-missing-review-is-a-halt.md`) and the governing spec `docs/concepts/fault-handling.md` (§ What counts as a verdict, and the known-faults row "A reviewer that ends without writing its review — a halt; the resumed run repeats that review"), both methods raise a new `MissingArtifactError(HaltError)` from inside the method instead. Because the raise happens before control returns to `process_task`, no post-review sidecar `step` is written, and the existing `planned:<N>` / `implemented:<N>` step resumes the same review attempt.

## Settings
- Testing: yes (two unit tests pinned by the task spec — the regression is silent)
- Logging: minimal
- Docs: no (`docs/concepts/fault-handling.md` already states the behaviour)

## Tasks

### Halt on a missing review

- [x] **Declare MissingArtifactError**
  Files: `orchestrator/agents.py`
  Add `class MissingArtifactError(HaltError)` directly after `NetworkError` (beside `RateLimitError` and `NetworkError`, before `PipelineStopError`). Its docstring states the fault it names: an agent ended its turn without writing the artifact its step requires. No body beyond the docstring, matching the two sibling subclasses. It must stay a `HaltError` subclass so `cli()`'s existing `except HaltError` arm in `orchestrator/main.py` reports it as `HALTED` (🟡) with the message's first line as the detail — no change in `main.py`, `compose()`, or `notify.py`.

- [x] **PlannerReviewer.review raises on an absent review file** (depends on Declare MissingArtifactError)
  Files: `orchestrator/agents.py`
  In `PlannerReviewer.review`, after `_run_claude` returns and after the existing `_write_session(plan_path, "planner", self.session_id)` (keep that write where it is), when `review_path` does not exist raise:
  ```python
  raise MissingArtifactError(
      f"Agent ended without writing its review\n{review_path}"
  )
  ```
  Restructure the tail so the absent-file case raises first; when the file exists, behaviour is exactly as now — the `ESCALATION` check (sidecar `escalation` + `step: escalated`, then `EscalationError`) first, then `return _has_signal(review_text, "REVIEW_PASS")`. The trailing `return False` for an absent file goes away, and the duplicated `if review_path.exists()` blocks collapse into one read of the file. Keep (or reword accurately) the comment that the verdict is read from the review file, not the chat output. Do not write any `step` in the raise path.

- [x] **PlanReviewer.review_plan raises on an absent review file** (depends on Declare MissingArtifactError)
  Files: `orchestrator/agents.py`
  In `PlanReviewer.review_plan`, after `_run_claude` returns, when `review_path` does not exist raise the same `MissingArtifactError(f"Agent ended without writing its review\n{review_path}")` (first line the fixed clause, path on the second line). When the file exists, behaviour is unchanged: escalation check first, then `return _has_signal(review_text, "PLAN_REVIEW_PASS")`. Remove the trailing `return False`. `review_plan` writes no sidecar on this path. Update the method docstring if it implies a missing file returns `False`.

  Guards for both methods (do not touch): `PlannerReviewer.plan` and the missing-plan `mark_skipped` branch in `process_task` stay as they are; `Implementer.implement` and `TestRunner.run` are untouched; the two final-attempt `read_text()` calls in `process_task` (`plan_review_path.read_text()` in the plan-review loop's `PipelineStopError`, `out_path.read_text()` in the implement loop's `max_iterations_message.format(...)`) stay as they are — they are now only reached when the file exists.

### Tests

- [x] **Pin the halt for both reviewer methods** (depends on PlannerReviewer.review raises on an absent review file, PlanReviewer.review_plan raises on an absent review file)
  Files: `tests/test_agents.py`
  Add `MissingArtifactError` to the `from orchestrator.agents import (...)` block. Add two tests beside `test_review_regression_no_escalation_returns_bool` and `test_review_plan_regression_no_escalation_returns_bool`, built like them — `plan_path = tmp_path / "01-slug.md"` with `plan_path.write_text("# Plan")`, a `review_path` under `tmp_path` (`01-slug-review-1.md` / `01-slug-plan-review-1.md`) that is never created — except `_run_claude` is replaced by a stand-in that writes nothing: `monkeypatch.setattr(agents, "_run_claude", lambda *a, **kw: ("output text", "sid-1"))`.
  - `PlannerReviewer(tmp_path).review(plan_path, review_path)` raises `MissingArtifactError`; `str(exc).splitlines()[0] == "Agent ended without writing its review"` and `str(exc).splitlines()[1] == str(review_path)`; the sidecar at `plan_path.with_suffix(".json")` exists (only `planner` is written) and has no `step` key.
  - `PlanReviewer(tmp_path).review_plan(plan_path, review_path)` raises `MissingArtifactError` with the same two-line message; `plan_path.with_suffix(".json")` does not exist (no sidecar written at all).
  Name each test and its section comment by behaviour (e.g. a section "A review that was never written halts"), not by any plan or roadmap coordinate. Run `uv run pytest` and confirm the full suite passes.
