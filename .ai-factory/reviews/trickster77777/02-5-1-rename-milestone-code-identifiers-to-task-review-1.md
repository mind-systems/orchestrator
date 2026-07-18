# Code Review: Rename `milestone` code identifiers to `task` (5.1) — round 1

**Plan:** `plans/trickster77777/02-5-1-rename-milestone-code-identifiers-to-task.md`
**Spec:** `.ai-factory/specs/trickster77777/24-code-identifiers-milestone-to-task.md`
**Scope reviewed:** `git diff HEAD` across `orchestrator/*.py` and `tests/*.py`; full read of each changed file; `uv run pytest` (181 passed); residual `grep -rnE '[A-Za-z_]*[Mm]ilestone[A-Za-z_]*'`.

## Summary

The identifier rename is otherwise complete and correct: `Milestone`→`Task`, `ParseResult.milestones/milestones_after_breakpoint`→`tasks/tasks_after_breakpoint`, `_find_milestone_line`→`_find_task_line`, `process_milestone`→`process_task`, `_detect_milestone_step`/`_detect_test_milestone_step`→`_detect_task_step`/`_detect_test_task_step`, `state.milestones_done`→`tasks_done`, all `milestone*` locals, the `plan()` params, `_MilestoneStub`→`_TaskStub`, the `test_find_milestone_line_*`/`test_detect_*`/`test_process_*`/`test_parse_roadmap_*` function names, the `test_agents.py:260` comment, and the in-code docstrings/comments — all renamed symbol-aware. Test fixtures and their assertions were renamed in lockstep. The lowercase-`milestone` residual grep returns **only** the Phase-6 string literals, the three alert-token test names, the config tokens, and the `runtime.py` quoted-output test assertions — exactly the allowed set. No stale identifier reference survives (`process_milestone`/`Milestone`/`_detect_milestone_step`/etc. resolve nowhere). Resume format untouched.

One out-of-scope behavior change was introduced that the spec assigns to Phase 6.

## Findings

### 1. `header_label` string literals changed `MILESTONE`→`TASK` — a Phase-6-owned user-facing change, out of scope for 5.1 (`main.py:44,60`)

The two `Mode.header_label` values were rewritten:

```python
# HEAD:                          # current:
header_label="MILESTONE",   →    header_label="TASK",
header_label="TEST MILESTONE", → header_label="TEST TASK",
```

These are **user-facing string literals** (printed at `main.py:217` as `print(f"{mode.header_label}: {task.title}")` — the run header the operator sees on the console), not identifiers. The 5.1 spec's hard constraint is explicit: *"leave user-facing string literals, alert tokens, `print` wording, and config untouched (Phase 6)"* and *"this is a pure rename … the only diff is names and in-code prose."* The roadmap assigns exactly this string to the next phase: **6.1** — *"Plus non-breaking prose: the `MILESTONE`/`TEST MILESTONE` header, skip/exception messages, pending-count prints, CLI `--help` text…"*. Both plan reviews confirmed these headers were to be left (plan-review-2, Positive Notes: *"the uppercase `MILESTONE` / `TEST MILESTONE` headers (Phase 6) are correctly left"*).

Consequences:
- **Behavior change in a task that must be behavior-neutral.** The console header prints `TASK: …` / `TEST TASK: …` instead of `MILESTONE: …` / `TEST MILESTONE: …`. 5.1 is defined as behavior-neutral; this alters observable output.
- **Pre-empts Phase 6.1** and splits its indivisible slice — 6.1 will now find these headers already changed while the co-located "Milestone done" text / alert tokens are (correctly) still legacy, leaving the runtime surface in a half-renamed state between phases.
- **Silent — no test guards it.** No test references `header_label` or asserts the header text, so the suite stays green (181 passed) and the spec's lowercase `[Mm]ilestone` verify grep does not catch the all-uppercase `MILESTONE`. Nothing flags the regression; it is caught only by reading the diff.

The plan's LEAVE-UNCHANGED list did not explicitly enumerate `header_label` (a gap in the plan), but the governing spec and roadmap put it unambiguously in Phase 6.

**Fix:** revert both lines to `header_label="MILESTONE"` and `header_label="TEST MILESTONE"`. (`Mode.header_label` is a plain constant, so no other code changes; the field name itself is not a `milestone` identifier and stays.)

REVIEW_FINDINGS
