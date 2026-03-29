## Code Review: Graceful stop in review loop

**Plan:** `.ai-factory/plans/07-graceful-stop-in-review-loop.md`
**Files changed:** `orchestrator/main.py`
**Files Reviewed:** 2 (`orchestrator/main.py`, `orchestrator/state.py`)
**Risk Level:** 🟢 Low

### Context Gates
- **ARCHITECTURE.md:** WARN — file not present, no architectural rules to verify against.
- **RULES.md:** WARN — file not present.
- **ROADMAP.md:** OK — milestone 7 "Graceful stop in review loop" matches the changes exactly.

### Verification

All three tasks implemented correctly:

1. **`_run_loop` helper** (lines 43-49): Iterates items, checks `state.stop_requested` before each, prints halt message and returns. Clean and minimal.
2. **Loop replacements** — all three call sites converted:
   - `_implement_loop` (lines 336-339): `enumerate` tuples unpacked via `item[0]`/`item[1]` — argument order to `process_milestone(project_dir, milestone, i, max_iterations)` preserved correctly.
   - `_refactor_loop` (lines 362-365): Same pattern, same correct argument mapping.
   - `run_review` inner `loop()` (line 454): Gains a stop check it previously lacked — this was the primary bug being fixed.
3. **Implement-to-review gate** (lines 393-395): Inserted after `_implement_loop` returns, before review-file cleanup and `run_review`. Ctrl+C during implement now prevents the review phase.

### Critical Issues

None.

### Suggestions

#### 1. Duplicate halt message in `run_implement_review`

**File:** `orchestrator/main.py`, lines 393-395

When stop is requested during `_implement_loop` and there are remaining milestones, two identical messages print:

```
>>> Stop requested — halting.

>>> Stop requested — halting.
```

The first comes from `_run_loop` (inside `_implement_loop`) when it encounters the next unprocessed item. The second comes from the new guard in `run_implement_review` on line 393-395.

**Fix:** Drop the print from the `run_implement_review` guard — `_run_loop` already informed the user, and even when the stop was requested during the *last* milestone (so `_run_loop` didn't print because the iterator was exhausted), the user already saw `_handle_sigint`'s message (`"Will stop after the current milestone finishes."`), which is sufficient context that the review phase won't start.

```python
# lines 393-395 — remove the print
if state.stop_requested:
    return
```

### Positive Notes

- Single extraction point for the stop-check logic eliminates a category of "forgot to add the guard" bugs for all future loop sites.
- Lambda closures capture only immutable function parameters (`project_dir`, `max_iterations`), so no late-binding surprises.
- `enumerate()` as an iterator to `_run_loop` is clean — the helper accepts any iterable without special-casing.
- SIGINT safety: `state.stop_requested` is a module-level bool; Python's GIL makes the signal-handler write and the `_run_loop` read effectively atomic.
