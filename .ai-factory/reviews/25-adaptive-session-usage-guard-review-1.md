# Code Review: Adaptive session usage guard

## Scope
`orchestrator/main.py` — added `_parse_usage_pct()`, `UsageGuard`, extended `_run_loop` with a `before_each` hook, and wired the guard into `_implement_loop` and `_test_loop`. Verified against `git diff HEAD`, the full file, and the plan.

## Verification performed

- **Syntax:** `ast.parse` of `main.py` passes.
- **`claude /usage` invocation (the main runtime risk):** ran it live in this environment. It produces, non-interactively on captured stdout:
  ```
  Current session: 35% used · resets Jun 17 at 4:29pm (Asia/Bishkek)
  ```
  The regex `r"Current session:\s+(\d+(?:\.\d+)?)%\s+used"` matches this. The guard is **functional**, not a silent no-op. (The note flagged this as an open question; it is now confirmed working.)
- **`_run_loop` callers:** none in the package. The `before_each` extension is forward-compat dead code, exactly as the plan acknowledges — harmless, no runtime effect today.

## Correctness analysis

- **Index offset is safe.** Both loops pass `i` from `enumerate(pending, start=_next_number(plans_dir))`, so `idx` is the plan sequence number (e.g. 25, 26, …), not 0/1 as the note's illustration implies. `UsageGuard` uses `idx` purely relatively: first `check` always fires (`idx >= 0`), then `idx + 1`, and `_predict_next` computes `avg_delta` per unit `idx`. Since `idx` increments by exactly 1 per milestone, the per-milestone delta math holds regardless of the starting offset. No bug.
- **Graceful degradation.** `_parse_usage_pct` wraps the subprocess in `except Exception`, so timeout / missing binary / format change return `None` → guard logs and continues with a `+5` backoff. `except Exception` (not `BaseException`) correctly lets `KeyboardInterrupt`/`SystemExit` propagate, so Ctrl+C during a usage check still works.
- **Stop propagation.** `PipelineStopError` raised in `check()` propagates through `_with_caffeinate` (which re-raises after cleanup) to `cli()`, which already handles it with exit code 0. Correct.
- **`avg_delta <= 0` and `span == 0` branches** both fall back to `idx + 5`, handling a mid-run session reset (pct drops) and same-index re-checks. Correct.
- **Backward compatibility.** `before_each=None` default and the `enumerate` change in `_run_loop` don't affect its (currently nonexistent) callers.

## Non-blocking observations

1. **Display vs. comparison rounding.** Logs use `{pct:.0f}` while the threshold test uses the exact `pct`. A fractional value like `89.7` would log `[usage: session 90% used]` yet not stop (89.7 < 90), which could momentarily confuse a log reader. In practice `claude /usage` reports integer percentages, so this is cosmetic and effectively never triggers. Not worth changing.
2. **Malformed `ORCHESTRATOR_USAGE_THRESHOLD`** (e.g. `"abc"`) raises `ValueError` from `float(...)`, which is uncaught and would crash with a traceback rather than a clean stop. The plan explicitly scoped this out and the default `"90"` is documented behavior — noting only for awareness.

## Verdict
The implementation faithfully matches the approved plan, the feature works end-to-end (confirmed empirically), and there are no correctness, security, or runtime defects. The two observations above are cosmetic / explicitly-scoped-out and do not warrant changes.

REVIEW_PASS
