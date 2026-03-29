# Patch: Graceful stop in review loop — Review 1

**Source review:** `.ai-factory/reviews/07-graceful-stop-in-review-loop-review-1.md`

## Fix 1: Remove duplicate halt message in `run_implement_review`

**File:** `orchestrator/main.py`, lines 393-395

**Problem:** When a user presses Ctrl+C during `_implement_loop` and there are remaining milestones, two identical `">>> Stop requested — halting."` messages print back-to-back. The first comes from `_run_loop` (called inside `_implement_loop`) when it checks `state.stop_requested` before the next item. The second comes from the guard at line 393-395 in `run_implement_review`.

When stop is requested during the *last* milestone (so `_run_loop`'s iterator is exhausted and it doesn't print), the user already saw `_handle_sigint`'s message (`"Will stop after the current milestone finishes."`), which is sufficient context.

**Fix:** Keep the `state.stop_requested` check and early return, but remove the `print()` call.

**Current code** (lines 393-395):
```python
        if state.stop_requested:
            print("\n>>> Stop requested — halting.")
            return
```

**Replace with:**
```python
        if state.stop_requested:
            return
```
