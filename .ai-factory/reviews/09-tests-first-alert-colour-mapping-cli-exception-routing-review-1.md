# Code review — 09 Tests-first: alert colour mapping + `cli()` exception routing

## Scope
Test-only change: new `tests/test_notify.py` and additions to `tests/test_main.py`. No product code modified.

## Verification
- `uv run pytest tests/test_notify.py tests/test_main.py` → **37 passed, 5 failed**. The 5 failures are exactly the red-by-design assertions the plan calls out:
  - `test_halt_alert_prefixed_yellow` (halt→🟡)
  - `test_cli_rate_limit_error_routes_to_halt` (RateLimitError→halt)
  - `test_cli_generic_exception_routes_to_halt_and_reraises` (generic→halt + re-raise)
  - `test_check_usage_limits_raises_halt_error_over_threshold` (usage→HaltError)
  - `test_process_milestone_resume_past_max_iterations_raises_halt_error` (resume-past-max→HaltError)
  All fail on clean assertions (`getattr(agents_module, "HaltError", None)` → `None`), not on `ImportError`/collection errors — the file imports and collects cleanly, satisfying the plan's key constraint.

## Correctness checks
- **Monkeypatch targets are the real call sites.** `main.py` imports `load_config`, `notify`, `subprocess`, and defines `run_implement` at module level (lines 8, 14, 15, 742); `cli()` and `_check_usage_limits` call them via those module-level names, so every `monkeypatch.setattr(main_module, ...)` binds to the symbol actually invoked. Confirmed live by the green `test_cli_pipeline_stop_error_routes_to_stop` (records `"stop"`) and the green usage-parse tests.
- **No network / non-determinism.** `send_telegram`, `subprocess.run`, `load_config`, `run_implement`, and `notify` are all patched; no HTTP, no `claude` CLI, no git, no LLM.
- **Resume test hits the intended raise.** The passing `plan-review-1.md` (ends with `PLAN_REVIEW_PASS`) clears the safety guard at `main.py:349`, and sidecar `review_failed:3` + present review artifact yields `("implement", 4, plan_path)`, so `impl_start (4) > max_iterations (3)` raises at `main.py:356` before any agent/git call. Captured stdout (`Resuming from step 'implement' (counter=4)`) confirms it reached that point. The `isinstance(exc.value, HaltError)` assertion pins the specific type, so it turns green only when task 05 re-points that raise — no false green.
- **Emoji/gating assertions match implementation.** `notify()` emits `f"{emoji} {text}"`; `.startswith("🔴"/"🟡"/"🟢")` is correct. Gating tests exercise all three guards (alert not listed, missing token, missing chat_id) and expect an empty recorder — matches the current no-op guards.
- **No `sent[0]` IndexError risk** in mapping tests: their configs list every alert type, so `send_telegram` is always reached.

No correctness, security, or runtime issues found.

REVIEW_PASS
