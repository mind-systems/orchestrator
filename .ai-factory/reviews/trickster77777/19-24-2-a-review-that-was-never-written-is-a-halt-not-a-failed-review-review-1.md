## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/agents.py`, `tests/test_agents.py`), plus the task's plan, plan-review and sidecar artifacts
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap — OK.** 24.2 is the first unchecked line in `.ai-factory/roadmaps/trickster77777.md`. The change follows its task spec `.ai-factory/specs/trickster77777/0058-a-missing-review-is-a-halt.md` point by point:
  - the new class and where it is declared;
  - both raise sites, with the exact two-line message;
  - no post-review `step` written;
  - the guards;
  - the two tests.
- **Governing spec — OK.** `docs/concepts/fault-handling.md` says under § What counts as a verdict that a verdict is not read from silence. Its known-faults row says a reviewer that ends without writing its review is a halt, and the resumed run repeats that review. The code now does both.
- **Architecture — OK.** The fault is detected inside the agent classes in `agents.py`, which also own artifact reading and the sidecar. There is no step-selection logic in `agents.py` and no new imports, so the dependency rules in `.ai-factory/ARCHITECTURE.md` still hold.
- **Rules — WARN.** There is no `.ai-factory/RULES.md`, so no project rules could be checked. This does not block anything.
- **Skill context — n/a.** There is no `.ai-factory/skill-context/aif-review/SKILL.md`.

### Verification

- **The new class.** `MissingArtifactError(HaltError)` is declared right after `NetworkError`, and its docstring names the fault.
  - `cli()` in `orchestrator/main.py` catches `HaltError` before the generic `except Exception` arm. It prints `HALTED — {e}` in full and reports `Outcome.HALTED` with `str(e).splitlines()[0]` as the detail.
  - The fixed first line `Agent ended without writing its review` is therefore the whole alert detail, and the path only appears in the console. This follows the `HaltError` docstring's rule that a message opens with a fixed clause.
  - Nothing between the reviewer call and `cli()` catches the error.
- **`PlannerReviewer.review`.**
  - `_write_session(plan_path, "planner", …)` still runs before the missing-file raise, so a resumed review keeps the planner session.
  - When the file exists, behaviour is unchanged: the escalation check runs first (sidecar `escalation` and `step: escalated`, then `EscalationError`), followed by `_has_signal(…, "REVIEW_PASS")`.
  - The two duplicated `exists()` blocks are now one read of the file.
- **`PlanReviewer.review_plan`.** It has the same shape. It writes no sidecar on the raise path, and its docstring documents the new raise.
- **Resume.** Both raises come before control returns to `process_task`, so no `plan_review_failed:N` or `review_failed:N` step is written. The sidecar keeps `planned:N` or `implemented:N`, which `resume.py` maps back to the same review attempt. The sidecar in this run (`implemented:1`) is the state that path produces.
- **Final-attempt stop messages.** The `plan_review_path.read_text()` and `out_path.read_text()` calls in `process_task` are now reached only after a reviewer returned, and it only returns when the file exists. The `FileNotFoundError` traceback path is closed.
- **Callers.** `review_plan` and `review` are called only from `main.py` (`_verify` and the plan-review loop). No other caller relied on a `False` return for a missing file.
- **Guards held.**
  - `PlannerReviewer.plan` and the missing-plan `mark_skipped` branch are untouched.
  - `Implementer.implement` and `TestRunner.run` are untouched.
  - `main.py`, `notify.py` and `compose()` are unchanged, which is correct because the new error is reported through the existing halt path.
- **Tests.**
  - The two new tests sit beside the regression tests they are modelled on, under a section header named by behaviour.
  - They replace `_run_claude` with a stand-in that writes nothing.
  - They check the two-line message, `planner == "sid-1"` with no `step` key for `review`, and that no sidecar exists for `review_plan`.
  - `uv run pytest`: 223 passed.

### Critical Issues

None.

### Positive Notes

- The fix sits exactly where the fault is detected. The resume point comes from the pre-review step writes that already exist, with no new sidecar state.
- Collapsing the duplicated `exists()` checks into one early raise and one file read makes both methods shorter and easier to read than before.
- The tests check the silent half of the regression: that no `step` is written. That is the part a raise-only test would miss.

REVIEW_PASS
