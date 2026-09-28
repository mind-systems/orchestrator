# A review that was never written is a halt, not a failed review

**Date:** 2026-09-28
**Source:** a `tradeoxy_core` run that died on its third plan-review attempt with `FileNotFoundError` on `.ai-factory/plan-reviews/190-59-6-engineslot-kind-retires-plan-review-3.md` after the plan reviewer ended its turn without writing the file

Governing spec: [fault-handling.md](../../../docs/concepts/fault-handling.md) — § What counts as a verdict (a verdict is not read from silence) and the known-faults row "A reviewer that ends without writing its review — a halt; the resumed run repeats that review".

## What is true now

Two reviewer methods in `orchestrator/agents.py` read a missing review file as a failed review:

- `PlanReviewer.review_plan(plan_path, review_path)` — after `_run_claude`, if `review_path` exists it checks for `ESCALATION` and returns `_has_signal(review_text, "PLAN_REVIEW_PASS")`; otherwise it returns `False`.
- `PlannerReviewer.review(plan_path, review_path, prev_review_path)` — after `_run_claude` and `_write_session(plan_path, "planner", …)`, the same shape: escalation check and `_has_signal(…, "REVIEW_PASS")` when the file exists, `False` when it does not.

`process_task` in `orchestrator/main.py` treats that `False` as a verdict:

- In the plan-review loop, on a non-final attempt it writes `step: plan_review_failed:<attempt>` and calls `planner_reviewer.plan(…, plan_review_path=plan_review_path)`, whose prompt tells the planner to read a review file that does not exist. On the final attempt (`attempt == max_iterations`) it builds `PipelineStopError(f"Plan failed\n\nLast review: {plan_review_path}\n\n{plan_review_path.read_text()}")`, and `read_text()` on the absent file raises `FileNotFoundError` — `cli()`'s last `except Exception` arm reports `ERRORED` and re-raises a traceback.
- In the implement loop, `_verify` returns `review(…)`'s `False`; on a non-final iteration `step` becomes `review_failed:<iteration>` and the implementer is told to read a missing review; on the final iteration `mode.max_iterations_message.format(…, content=out_path.read_text())` raises the same `FileNotFoundError`.

The sidecar step before each review is already the right resume point: `planned:<N>` is written before plan-review attempt `N`, and `implemented:<N>` before review iteration `N`. `resume.py` dispatches `planned:N` → `("plan_review", N)` and `implemented:N` → `(verify_step, N)`, so a run that stops before the post-review step write resumes at that same review.

`HaltError` (`agents.py`) is the operational halt: `cli()` prints `HALTED — {e}` in full and reports `Outcome.HALTED` (🟡) with `str(e).splitlines()[0]` as the detail; every halt message opens with a fixed clause and carries anything variable on a later line. Its subclasses today are `RateLimitError` and `NetworkError`.

## What must be true after

A new `MissingArtifactError(HaltError)` in `orchestrator/agents.py`, declared beside `RateLimitError` and `NetworkError`, its docstring stating the fault it names: an agent ended its turn without writing the artifact its step requires.

`review_plan` and `review` each, when `review_path` does not exist after `_run_claude` returns, raise:

```python
raise MissingArtifactError(
    f"Agent ended without writing its review\n{review_path}"
)
```

The first line is the fixed clause the `HALTED` alert carries; the path is on the second line, printed by the console only. Where the file exists, both methods behave exactly as now — escalation first, then the PASS signal.

The raise happens inside the reviewer method, before control returns to `process_task`, so no post-review `step` is written: the sidecar keeps `planned:<N>` or `implemented:<N>`, and the next run repeats that same review attempt. The two `read_text()` calls in the final-attempt stop messages are then only reached when the file exists, and stay as they are.

Tests in `tests/test_agents.py`, one per method, beside `test_review_regression_no_escalation_returns_bool` and `test_review_plan_regression_no_escalation_returns_bool` and built like them — a `# Plan` file at `tmp_path / "01-slug.md"`, a `review_path` under `tmp_path` that is never created — except that `_run_claude` is replaced by a stand-in that writes nothing: `monkeypatch.setattr(agents, "_run_claude", lambda *a, **kw: ("output text", "sid-1"))`. Calling `PlanReviewer(tmp_path).review_plan(plan_path, review_path)` and `PlannerReviewer(tmp_path).review(plan_path, review_path)` each raises `MissingArtifactError`, whose message's first line is `Agent ended without writing its review` and whose second line is `str(review_path)`; and the sidecar at `plan_path.with_suffix(".json")` carries no `step` key — `review` writes only `planner` there, `review_plan` writes no sidecar at all. A regression here is silent — the run carries on as if the review had failed — so it is tested.

## What breaks on contact

- The affected set is every read of a reviewer's output file in `process_task`. Sweep: `rg -n "read_text\(\)" orchestrator/main.py`. Run now, it reaches four reads: the plan-review loop's final-attempt `PipelineStopError` (`plan_review_path.read_text()`) and the implement loop's final-iteration `mode.max_iterations_message.format(…, content=out_path.read_text())` — the two this task's targets make safe, since each now follows a reviewer call that returned only because its file exists; the safety guard's `_plan_review_files[-1].read_text()`, which reads a file found by `glob` and so cannot meet an absent one; and `_resolve_roadmap_relpath`'s `roadmap_file.read_text()`, which is not a review. The implementer's `feedback_path` for iteration `N + 1` is the review of iteration `N`, which now exists whenever that review returned.
- No existing test relies on a missing review returning `False`: `rg -n "is False" tests/test_agents.py` reaches only `_has_signal`/`_has_escalation` cases, and the reviewer tests in `tests/test_agents.py` all write their artifact through `_stub_run_claude_writing`. `tests/test_main.py` never reaches either method: of its two `process_task` tests, `test_process_task_escalated_sidecar_raises_without_constructing_agents` replaces the agent classes wholesale, and `test_process_task_resume_past_max_iterations_raises_halt_error` halts on the resume-past-budget check before any review runs.
- The skills-side `orchestrator-artifacts` engine states nothing about an absent review file, so this change needs no mirror there.
- `TestRunner.run` always writes its output file, including on a missing `## Test Command`; test mode's verify step cannot meet this fault and is untouched.
- `PlannerReviewer.plan`'s own handling of a missing plan — `process_task` calling `mark_skipped` when `plan_path` does not exist after planning — is a separate behaviour and stays as it is.
- `Implementer.implement` has no artifact of its own to check; it is untouched.
- The halted attempt's elapsed time is not written to the sidecar, because the `_write_session(plan_path, "elapsed", …)` after each reviewer call is not reached — the same as any other halt raised from inside an agent call.
- `cli()`'s `except HaltError` arm, `compose()`, and `notify.py` need no change: a `MissingArtifactError` is a `HaltError` and is reported as one.
