# Review: Total run time in terminal Telegram alerts

## Scope
Changes to `orchestrator/state.py` and `orchestrator/main.py` adding a run-start timestamp and appending `Ran for <elapsed>` to the three terminal Telegram alerts.

## Verification

- **`state.py`** — `run_started: float | None = None` added alongside the existing module globals, matching the typed-global style. `state.py` is the cross-layer global module (ARCHITECTURE dependency rules allow import from any layer), so this is the correct home. No dependency-direction violation.
- **`_run_elapsed()`** — defined immediately after `_fmt_elapsed`, before every call site. The `None` guard returns `"unknown"`, so a notify can never crash on a missing timestamp. Reuses `_fmt_elapsed`; no duplicated formatting. `state` and `time` are already imported at module top.
- **Timestamp set** — `state.run_started = time.monotonic()` is the first statement of both `run_implement()` and `run_test()`, before `signal.signal(...)` and `_with_caffeinate(...)`. `_with_caffeinate`'s own local `start` and its console prints are untouched, keeping the two timing concerns independent.
- **Alert sites** — all three terminal alerts append `\nRan for {_run_elapsed()}`: done (`_run_dynamic_loop`), `PipelineStopError`, and `RateLimitError`. The alert `type` strings (`"done"`/`"stop"`) are unchanged, so `telegram_alerts` filtering in `notify()` is preserved. Multi-line text is URL-encoded by `send_telegram` and delivered as a single message body — `\n` is safe.

## Reachability / ordering check
`load_config()` runs before the `try` block in `cli()`; both exception handlers can only fire from inside `run_implement`/`run_test`, by which point `run_started` is already set. The defensive `"unknown"` branch remains a safety net but is not reachable on the normal path.

## Untouched surfaces (per plan)
- The four `milestone` notify calls are unchanged.
- The startup early-return "All milestones are done!" path sends no alert and is unchanged.
- No new alert types or config keys.

No correctness, type, security, or race issues found.

REVIEW_PASS
