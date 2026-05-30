# Code Review: Sidecar robustness — three follow-up fixes

**Plan:** `plans/19-sidecar-robustness-three-follow-up-fixes.md`
**Diff scope:** `orchestrator/agents.py` (`_read_sessions`, `_write_session`),
`orchestrator/main.py` (`process_milestone` review loop, `process_test_milestone`
test loop).

## Verification against the plan

All four tasks were implemented and match the plan's target shapes byte-for-byte:

- **Task 1** — `_read_sessions` (`agents.py:24-31`) wraps `json.loads(p.read_text())`
  in `try/except (json.JSONDecodeError, OSError)` returning `{}`. Matches the
  target snippet exactly. ✓
- **Task 2** — `_write_session` (`agents.py:34-40`) writes to
  `p.with_suffix('.json.tmp')` then calls `os.replace(tmp, p)`. `os` is already
  imported (`agents.py:6`). No new imports added. Matches target shape. ✓
- **Task 3** — `process_milestone()` (`main.py:270-277`) now calls
  `_write_session(plan_path, "step", f"review_failed:{iteration}")` **before**
  the `if iteration == max_iterations: raise PipelineStopError(...)` guard.
  Reordering is correct. ✓
- **Task 4** — `process_test_milestone()` (`main.py:694-704`) now calls
  `_write_session(plan_path, "step", f"test_run_failed:{iteration}")` after
  the bridge-patch write at `main.py:697-698` and before the
  `if iteration == max_iterations: raise PipelineStopError(...)` guard. The
  bridge-patch write is preserved at its original position as the plan
  required. ✓

## Correctness analysis

### Path semantics for the tmp file

`plan_path.with_suffix('.json')` yields e.g. `19-foo.json`; calling
`.with_suffix('.json.tmp')` on that yields `19-foo.json.tmp` (Python's
`Path.with_suffix` replaces only the final suffix). Because the tmp lives in
the same directory as the target, `os.replace` will not hit `EXDEV` (cross-
device rename). Behavior is portable to POSIX and Windows (Python documents
`os.replace` as atomic on both). ✓

### Resume routing after Fix 2

`_detect_milestone_step` (`main.py:103-112`, `main.py:537-544`) explicitly
matches `plan_review_failed:`, `review_failed:`, and `test_run_failed:`
prefixes, so the freshly-written step value will route correctly on the next
run, hitting the implement-iteration path instead of overwriting `review-1.md`
/ `test-1.txt`. ✓

### Existing patch-bridge ordering in `process_test_milestone`

The bridge patch write happens **before** `_write_session(... "test_run_failed:")`
(`main.py:697-699`). That is the right order: if the process dies between the
patch write and the step write, the next run will not see the `test_run_failed:`
step, so it falls back to whatever step is still recorded (probably
`"implemented"`), restarts the iteration, and overwrites the patch anyway —
no inconsistency. The reverse order (step first, patch second) would be
strictly worse because a crash could leave a step pointer to a missing patch
file. Good. ✓

### `process_refactor_milestone` was correctly left alone

`process_refactor_milestone` (`main.py:400-408`) has the same
`if iteration == max_iterations: raise PipelineStopError(...)` structure but
does **not** write a per-iteration `step` value at all (only `elapsed`). The
plan deliberately scoped Fix 2 to `process_milestone` and
`process_test_milestone`, and that matches the actual codebase — there is no
`refactor_failed:` step type tracked by `_detect_milestone_step`. No regression
from omitting it. ✓

### Sidecar JSON pre-existing in the repo is fine

The newly-committed `19-sidecar-robustness-three-follow-up-fixes.json`
currently contains `{"planner":..., "step":"implemented", "elapsed":"279",
"implementer":...}`. After this milestone is marked done, the next run's
`_detect_milestone_step` will see the unchecked roadmap line absent (it gets
checked by `mark_done`), so this sidecar will not be revisited. No
side effects from the trailing in-progress state. ✓

## Concerns (non-blocking)

### 1. `_write_session`'s internal read is still unguarded — Fix 1 is partially defeated

**File:** `orchestrator/agents.py:36`

```python
def _write_session(plan_path: Path, key: str, value: str) -> None:
    p = plan_path.with_suffix('.json')
    data = json.loads(p.read_text()) if p.exists() else {}   # ← unprotected
    ...
```

The plan explicitly deferred this ("Do not alter semantics beyond the
atomic-replace pattern") and the plan-review accepted it as a scope choice,
so this is **not a deviation from the plan**. But it is worth surfacing
again now that the code is in front of us:

The advertised benefit of Fix 1 ("crash-resilience: corrupt sidecar →
treated as no recorded sessions") only holds for the **read** path
(`_detect_milestone_step` → `_read_sessions`). The **first subsequent write**
in the same run will still call `json.loads(p.read_text())` on the corrupt
file and raise `JSONDecodeError`, which propagates out of
`PlannerReviewer.plan()` and crashes the orchestrator. So a corrupt sidecar
inherited from a previous `kill -9` (the exact failure mode Fix 1 is
described as fixing) still kills the next run — `_read_sessions` recovers,
then `_write_session` immediately re-trips on the same file.

The plan-review proposed a one-line fix and the plan declined it. Now that
Fix 3 makes new corruption nearly impossible, the residual risk is only
legacy / out-of-band corruption (manual edits, pre-Fix-3 crashes, parallel
non-orchestrator writers). Whether that is worth a follow-up is a judgment
call — I am not blocking this milestone on it. Recommended action: track as
a tiny follow-up in `ROADMAP.md` or `notes/` so it does not get lost.

### 2. Stale `*.json.tmp` after `kill -9` between `tmp.write_text` and `os.replace`

**File:** `orchestrator/agents.py:38-40`

If the process is `kill -9`'d in the gap between `tmp.write_text(...)` and
`os.replace(tmp, p)`, a sibling `*.json.tmp` is left behind in
`.ai-factory/plans/`. It is harmless (not committed if the project ignores
`*.tmp`, not read by anything, overwritten on the next call), and the plan-
review already noted this. The current `.gitignore` is not in the diff so
I cannot confirm whether `*.tmp` is excluded — if it is not, a `kill -9`
followed by a successful run could leave an orphan `.json.tmp` that ends up
in `git status`. Cosmetic, no action required.

### 3. Resume after `PipelineStopError` hitting `max_iterations` without bumping the env var

**Files:** `orchestrator/main.py:251`, `main.py:676`

Pre-existing behavior, surfaced more clearly by Fix 2 (the plan-review
already flagged this): with `step=review_failed:N` where `N == max_iterations`,
`impl_start = N+1 = max_iterations+1`, so `range(impl_start, max_iterations+1)`
is empty. The implement/review loop body **never executes** and control falls
straight through to `mark_done()` + `_git_commit()` — i.e. the orchestrator
commits broken code as done. Before Fix 2 the same scenario at least
restarted iteration 1 (the original `review-1.md` overwrite bug), so this is
a behavioral trade: Fix 2 trades "buggy retry that loses history" for "silent
skip-to-commit if you forget to bump `ORCHESTRATOR_MAX_ITERATIONS`."

This is out of scope for the current milestone but is the natural follow-up.
A defensive guard like

```python
if impl_start > max_iterations:
    raise PipelineStopError(
        f"Resume at iteration {impl_start} exceeds max_iterations "
        f"({max_iterations}); bump ORCHESTRATOR_MAX_ITERATIONS to continue."
    )
```

at the top of both implement/review loops would close this hole. Not a
blocker for this PR.

## Positive notes

- Implementation matches the plan exactly — no scope creep, no incidental
  edits.
- The reordering in `process_test_milestone` correctly preserved the bridge
  patch write at its original position (one of the easier subtleties to
  break).
- `os.replace` was reached for instead of `os.rename` — correct choice for
  Windows portability, even though the project is primarily targeted at
  macOS/Linux per the environment metadata.
- The `try/except (json.JSONDecodeError, OSError)` in `_read_sessions`
  correctly includes `OSError` for transient read failures, not just JSON
  malformation. Matches the plan and the spec note.

## Summary

The implementation is correct and matches the plan task-for-task. The three
concerns above are either explicit deferrals from the plan (#1), cosmetic
(#2), or pre-existing behavior surfaced more clearly by Fix 2 (#3). None
warrants blocking this milestone.

REVIEW_PASS
