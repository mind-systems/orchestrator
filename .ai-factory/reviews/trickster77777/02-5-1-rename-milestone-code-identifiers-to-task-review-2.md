# Code Review: Rename `milestone` code identifiers to `task` (5.1) — round 2 (re-review)

**Plan:** `plans/trickster77777/02-5-1-rename-milestone-code-identifiers-to-task.md`
**Spec:** `.ai-factory/specs/trickster77777/24-code-identifiers-milestone-to-task.md`
**Scope reviewed:** `git diff HEAD` / `git status` across `orchestrator/*.py` and `tests/*.py`; re-read of the cited file; `uv run pytest` (181 passed); residual `[Mm]ilestone` and uppercase `MILESTONE` greps.

## Verdict on round-1 findings

### Finding 1 — `header_label` `MILESTONE`→`TASK` out of scope (`main.py:44,60`): **Fixed**

Current content, re-read from disk:

```python
44:    header_label="MILESTONE",
60:    header_label="TEST MILESTONE",
```

Both `Mode.header_label` values are restored to their HEAD state — the Phase-6-owned console-header string literals are once again left byte-for-byte, so 5.1 stays behavior-neutral and does not pre-empt Phase 6.1. An uppercase `MILESTONE` grep over `orchestrator/*.py tests/*.py` now returns *only* these two header lines (the exact set Phase 6.1 owns), and the `Mode.header_label` field name itself is not a `milestone` identifier, so no further change was warranted. The two-line revert introduced nothing else — `main.py`'s diff shrank by exactly the reverted pair and the rest of the rename is untouched.

## Full re-review

Re-verified the whole change end-to-end, not just the fix:

- **Identifier rename complete and symbol-aware.** `Milestone`→`Task`, `ParseResult.milestones`/`milestones_after_breakpoint`→`tasks`/`tasks_after_breakpoint`, `_find_milestone_line`→`_find_task_line`, `process_milestone`→`process_task`, `_detect_milestone_step`/`_detect_test_milestone_step`→`_detect_task_step`/`_detect_test_task_step`, `state.milestones_done`→`tasks_done`, the `plan()` params, all `milestone*` locals, `_MilestoneStub`→`_TaskStub`, and every `test_find_milestone_line_*`/`test_detect_*`/`test_process_*`/`test_parse_roadmap_*` function name. No stale identifier resolves anywhere.
- **Co-located Phase-6 literals correctly preserved.** On the mixed lines (`main.py` 241, 311, 359, 382, 384, 401) only the embedded identifier was renamed (`task.title`/`task.slug`/`result.tasks`/`result.tasks_after_breakpoint`); the surrounding "Milestone done" / "milestone" token / "pending milestones" / exception text stays byte-for-byte. `runtime.py:39` renames `state.tasks_done` while keeping the "milestones done" summary text. `notify.py:15` `_FAIL_ALERTS = {"milestone-fail"}` untouched.
- **Residual `[Mm]ilestone` grep is exactly the allowed set** — Phase-6 string literals (`main.py` skip/notify/exception/print/argparse/`milestone-fail`), `notify.py:15`, `runtime.py:23,39`, the config tokens (`test_config.py:111,115`), the three protected alert-token test names (`test_notify.py:41,55`, `test_main.py:848`), and the `test_runtime.py` assertions/docstrings that quote the still-legacy "milestones done"/"current milestone finishes" output. No identifier, docstring, or comment survives.
- **In-code prose renamed** — docstrings/comments in `agents.py` (70, 274), the `agents.py:304` prompt f-string, `resume.py` (61, 103), `roadmap.py`, `main.py` (1, 178, 199, 367, 423, 439, 454), `notify.py` (14, 17), and the `test_agents.py:260` comment.
- **Test fixtures renamed in lockstep with their assertions** (`test_roadmap.py` title strings and `result.tasks*` reads; `_TaskStub.title = "Some task"`), so no test asserts against a stale string.
- **Behavior-neutral / resume-safe.** No on-disk sidecar key, artifact-filename scheme, or `step` value changed; the rename is names + prose only. `uv run pytest` → **181 passed**.

No new bugs, type mismatches, or runtime-break risks found. The one prior finding is resolved and the change now matches the plan and spec exactly.

REVIEW_PASS
