## Plan Review Summary

**Plan:** 24.2 — A review that was never written is a halt, not a failed review
**Files Reviewed:** plan; task spec `.ai-factory/specs/trickster77777/0058-a-missing-review-is-a-halt.md`; `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/resume.py`, `tests/test_agents.py`; `docs/concepts/fault-handling.md`, `docs/pipeline.md`, `docs/concepts/outcomes.md`; `.ai-factory/ARCHITECTURE.md`
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap — OK.** 24.2 is the first unchecked line in `.ai-factory/roadmaps/trickster77777.md`, directly after the `[x]` 24.1. The plan's `# Plan:` heading matches the contract line. The contract line's `Spec:` tag resolves to spec 0058, which the plan follows item by item: the class, both raise sites, the exact two-line message, no post-review step, the guards, and the two tests.
- **Governing spec — OK.** `docs/concepts/fault-handling.md` already says this under § What counts as a verdict ("Nor is a verdict read from silence…") and in the known-faults row "A reviewer that ends without writing its review | A halt; the resumed run repeats that review". `docs/pipeline.md` says the same in its file-protocol paragraph. `docs/concepts/outcomes.md` points to that catalogue for halt causes and has no list of its own that would need a new entry. The plan's `Docs: no` is therefore correct: the docs describe this behaviour before the code has it, as they should.
- **Architecture — OK.** The raise stays inside the agent class that reads the artifact. That matches how the existing `ESCALATION` detection is wired, and it adds no step-selection logic to `agents.py`. The only step effect is a *missing* post-review write in `main.py`. No new imports. `agents.py` stays well under the 700-line smell threshold.
- **Rules — WARN.** There is no `.ai-factory/RULES.md`, so no explicit rules could be checked. This does not block anything.
- **Skill context — n/a.** There is no `.ai-factory/skill-context/aif-review/SKILL.md`.

### Verification against the codebase

- **Class placement.** `HaltError` → `RateLimitError` → `NetworkError` → `PipelineStopError` → `EscalationError` is the order in `agents.py`. Putting `MissingArtifactError(HaltError)` between `NetworkError` and `PipelineStopError` matches the spec's "beside `RateLimitError` and `NetworkError`". The `HaltError` docstring requires "a fixed clause … anything variable … on a later line". The pinned message `"Agent ended without writing its review\n{review_path}"` meets that requirement.
- **Reporting path.** `cli()` in `main.py` has `except HaltError` before the catch-all `except Exception`. It prints `HALTED — {e}` in full and reports `Outcome.HALTED` with `str(e).splitlines()[0]`. None of `run_implement`, `run_test` or `process_task` catches `HaltError` or `Exception`: the only `except` clauses in `main.py` are in `cli()`. So the new error reaches that arm with nothing in between. No change is needed in `main.py`, `compose()` or `notify.py`, as the plan says.
- **Resume correctness.**
  - `process_task` writes `planned:<N>` before plan-review attempt N: `planned:{counter}` after planning, and `planned:{attempt + 1}` after each revision. It writes `implemented:<iteration>` before each `_verify`.
  - `resume.py` `_validate_sidecar_step` accepts `planned:N`/`implemented:N` without checking the disk. Dispatch maps them to `("plan_review", N)` and `(verify_step, N)`.
  - In the implement loop, `step == mode.verify_step and iteration == counter` skips re-implementation and goes straight to verify.
  - Raising from inside the reviewer skips every later `_write_session(..., "step", ...)`. The resumed run therefore repeats exactly the review that was lost.
- **`PlannerReviewer.review`.** It calls `_write_session(plan_path, "planner", self.session_id)` right after `_run_claude`. The plan keeps that write before the raise, so a resumed review keeps the planner session. The duplicated `if review_path.exists()` blocks ending in `return False` are as the plan describes; collapsing them is safe.
- **`PlanReviewer.review_plan`.** Its only sidecar writes are on the escalation path, so the plan's test assertion that "no sidecar at all" exists holds. Its docstring ("Returns True if passed") does not claim that a missing file returns `False`, so the plan's conditional docstring update will be a no-op or a harmless clarification.
- **Downstream `read_text()` calls.**
  - `plan_review_path.read_text()` in the final-attempt `PipelineStopError` and `out_path.read_text()` in `max_iterations_message.format` are now reached only after the reviewer returned, which means the file exists.
  - The safety guard's `_plan_review_files[-1].read_text()` reads a file found by `glob`.
  - The plan's guard to leave these alone is correct.
- **Test mode is unaffected.** `TestRunner.run` always writes `output_path`, including on a missing `## Test Command`, so `_verify` in test mode never meets this fault.
- **Tests.**
  - `_stub_run_claude_writing` and the two named sibling tests exist at the named positions in `tests/test_agents.py`.
  - The replacement stub `lambda *a, **kw: ("output text", "sid-1")` matches the `(output, session_id)` tuple that both methods unpack.
  - `MissingArtifactError` is not yet in the import block; the plan adds it.
  - No existing test depends on a missing review returning `False`. The current suite passes (`uv run pytest`: 221 passed).
- **Cross-repo mirror.** The spec's "What breaks on contact" section says the skills-side `orchestrator-artifacts` engine says nothing about an absent review file. No directory layout, artifact name, PASS signal or sidecar field changes, so nothing needs mirroring.

### Critical Issues

None.

### Positive Notes

- The plan places the fix where the fault is detected, inside the reviewer. The resume point then comes for free from the existing pre-review step writes, with no new sidecar state.
- The guards are thorough and accurate: `plan()`/`mark_skipped`, `Implementer.implement`, `TestRunner.run`, and the two final-attempt `read_text()` calls.
- The tests check the silent part of the regression: that no `step` key is written. Checking only that the error is raised would miss it.
- It correctly keeps the `planner` session write before the raise, which a resumed review depends on.

PLAN_REVIEW_PASS
