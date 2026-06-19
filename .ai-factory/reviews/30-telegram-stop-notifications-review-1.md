# Code Review: Telegram stop notifications (attempt 1)

## Scope
Reviewed changes to `orchestrator/config.py`, `orchestrator/notify.py`, `orchestrator/main.py`, and `orchestrator.json.example` against the plan at `.ai-factory/plans/30-telegram-stop-notifications.md`.

## Verification performed
- Confirmed both fields default to `None` on the dataclass and are absent from the `required` list, so existing configs without the keys still load.
- Confirmed `data.get(...) or None` coerces `""` → `None`, making the `config.telegram_bot_token and config.telegram_chat_id` truthiness guard in `cli()` correct (empty string → silent no-op).
- Traced exception propagation: `PipelineStopError`/`RateLimitError` raised inside the loops propagate through `_with_caffeinate` (catches `Exception`, prints, then `raise`) up to the `cli()` handlers. The notification fires on the real halt paths.
- Checked `str(e).splitlines()[0]` for an empty-message `IndexError`: every `PipelineStopError` raise uses an explicit f-string message, and both `RateLimitError(result_text)` sites are gated on `result_text` containing `"hit your limit"`/`"resets"`, so the message is always non-empty. No crash risk.
- `send_telegram` wraps the request in `try/except Exception` and only prints on failure, so a network error never crashes the process or re-raises out of the exception handler. `urlencode` correctly escapes `chat_id` and the multi-line `text`.
- `orchestrator.json.example` remains valid JSON (trailing comma added correctly).
- No new third-party dependency; `urllib` is stdlib.

## Findings

### Nit (non-blocking): unused import
`orchestrator/notify.py` imports `urllib.error` but never references it — the `except Exception` is broad and does not need it. Harmless; safe to drop. Not worth a fix iteration on its own.

## Conclusion
No correctness, security, or runtime-breakage issues. The change is well-scoped, fails safe, and matches the plan.

REVIEW_PASS
