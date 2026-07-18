# Plan Review: Rename `milestone` code identifiers to `task` (5.1)

**Plan:** `plans/trickster77777/02-5-1-rename-milestone-code-identifiers-to-task.md`
**Spec:** `.ai-factory/specs/trickster77777/24-code-identifiers-milestone-to-task.md`
**Roadmap:** `.ai-factory/roadmaps/trickster77777.md` → Phase 5 → 5.1
**Risk Level:** 🟡 Medium — the plan is meticulous and mostly correct, but two in-scope `milestone` prose occurrences are unaccounted for, and both would surface at the plan's own Task 10 Verify grep.

## Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): OK. A behavior-neutral symbol rename touches no module boundary or dependency direction. No conflict.
- **Rules** (`.ai-factory/RULES.md`): absent — WARN (optional file, no rules to check).
- **Roadmap alignment**: OK. Task maps cleanly to Phase 5 → 5.1 in the named roadmap; the plan correctly scopes out Phase-6 strings/tokens (6.1) and Phase-7 prompt bodies (7.1), and its `agents.py:304` boundary assumption is sound — that prompt f-string is claimed by neither Phase 6 (not an alert token / "Milestone done" text / `print` wording / config) nor Phase 7 (`.md` bodies), so renaming it here is required for the Verify grep to come clean.

## Critical Issues

### 1. `_git_commit` docstring (`main.py:178`) is omitted from Task 4's docstring rename list
Task 4 enumerates the main.py docstrings to rename as lines **1, 199, 367, 423, 439, 454** and, for `_git_commit`, renames only the `milestone_title` param (line 177 + uses 187, 189). It does **not** list line 178:

```python
def _git_commit(project_dir: Path, milestone_title: str) -> None:
    """Stage all changes and commit after a completed milestone."""
```

`"after a completed milestone"` is an in-code docstring using the roadmap-unit word — exactly what the spec puts in scope ("a renamed symbol with a stale docstring is an incoherent half-state") and not a Phase-6 string literal. Following Task 4's enumerated list literally, an implementer leaves it, and Task 10's grep then surfaces `main.py:178` as a residual that is neither (a) a Phase-6 string literal nor (b) one of the three alert-token test names — violating Task 10's "No identifier, docstring, or comment may survive." Add line 178 → "completed task" to Task 4.

### 2. `test_agents.py` is not addressed by any task, but carries an in-scope `milestone` comment
The plan's task list covers `test_roadmap.py` (Task 7), `test_main.py` (Task 8), `test_runtime.py` (Task 9), and lists `test_notify.py` / `test_config.py` as LEAVE UNCHANGED. **`test_agents.py` appears nowhere** — neither as a file to change nor as an exception. It contains:

```python
# tests/test_agents.py:260
# Task 5: RED case -- semver ordering (fixed in milestone 2.2)
```

`"fixed in milestone 2.2"` is an in-code comment naming the roadmap unit — in Phase 5's scope (the spec's Verify grep explicitly spans `tests/*.py`, and Phase 5 renames in-code comments). Left as-is, Task 10's grep (`grep -rnE '…' … tests/*.py`) flags `test_agents.py:260`, which is not in the allowed residual set — so the plan as written cannot satisfy its own "No other … survives" acceptance. Add a task (or fold into Task 8's phase) renaming this comment to "task 2.2", or, if it is deliberately excluded, list it explicitly in the LEAVE UNCHANGED set with a rationale. Silent omission is the defect either way.

## Positive Notes
- Line references are otherwise well-grounded: spot-checked `_git_commit` param (177/187/189), the `notify`/exception multi-line strings (241, 311, 359, 382, 401–402), `state.milestones_done` sites (239, 357, 458, 471), `_MilestoneStub` (916, 923), and the three protected alert-token test names (`test_notify.py:41,55`, `test_main.py:848`) — all match the code exactly.
- The one-hard-constraint framing (symbol-aware rename; identifier renamed, string literal kept byte-for-byte even when both sit on one line) is correctly applied line-by-line, including the split of the 401–402 `PipelineStopError` string.
- Case-insensitive-safe: the uppercase `"MILESTONE"` / `"TEST MILESTONE"` headers (Phase 6) are correctly left and do not appear in the `[Mm]ilestone` grep, so no false Verify hit — consistent with leaving them.
- The single-commit rationale is correct: no proper sub-slice keeps the suite green (renaming a symbol without its test consumer breaks import/collection).

## Verdict
Two in-scope `milestone` occurrences (`main.py:178`, `test_agents.py:260`) are unaccounted for and both would trip Task 10's Verify grep. Close them (extend Task 4's docstring list; add `test_agents.py` to the task set or the exception list) and the plan is ready. Both fixes stay inside the milestone's file boundary — they are findings, not deferred observations.
