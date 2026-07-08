# Tests-first — alert colour mapping and cli() exception routing (for task 05)

**Date:** 2026-07-09
**Source:** conversation context

## Why this is its own milestone

Task 05 changes how run outcomes are signalled by colour. The colour/type mapping and the `cli()` exception→alert-type routing are **silent-failure** surfaces (a wrong colour or a mis-routed exception sends the wrong signal with no crash — per `test-philosophy`, exactly what to test). There is **zero** current coverage — no test touches `notify`, the emoji prefix, or the exception handlers. This milestone writes those tests **first**; task 05 turns them green. Written before 05, the assertions on the not-yet-built behaviour (yellow `halt`, `HaltError`) are **red by design** — that is the TDD signal, not a defect; the assertions on unchanged behaviour (`milestone`/`done` green, `PipelineStopError` red) are green immediately.

## What to test (silent-failure surfaces only)

New `tests/test_notify.py`:
- The emoji prefix is a pure mapping `alert_type → prefix`: `stop` → 🔴, `halt` → 🟡, `milestone`/`done` (and any unknown) → 🟢. Monkeypatch `send_telegram` (or `urllib`) to capture the outgoing text and assert its leading emoji — never hit the network.
- Gating stays intact: an `alert_type` absent from `config.telegram_alerts` sends nothing; missing `telegram_bot_token`/`telegram_chat_id` sends nothing (silent no-op).

Additions to `tests/test_main.py`:
- `cli()` routing: monkeypatch `notify` to record `(text, alert_type)` and monkeypatch `run_implement`/`run_test` to raise — assert `PipelineStopError` → `"stop"`, `HaltError` (and its `RateLimitError` subclass) → `"halt"`, and a generic `Exception` → `"halt"` **and is re-raised** (traceback survives).
- Exception type at the source: with a stubbed usage reader returning an over-threshold percentage, `_check_usage_limits` raises `HaltError` (not `PipelineStopError`); a resume `step`/counter past `max_iterations` raises `HaltError`. (These assert the 05 re-pointing; red until 05 lands.)

## What NOT to test (loud / out of scope)

- The actual Telegram HTTP call and its network-error swallowing — loud/side-effecting, already a guarded no-op.
- Agent LLM calls, git subprocess, signal-handler wiring — loud or non-deterministic.
- Do not assert on message wording beyond the emoji prefix and the alert-type — wording is not a silent-failure surface.

## Verify

- `uv run pytest tests/test_notify.py tests/test_main.py` collects and runs; the unchanged-behaviour assertions pass now; the new-behaviour assertions are red until task 05 is implemented, then all green.
