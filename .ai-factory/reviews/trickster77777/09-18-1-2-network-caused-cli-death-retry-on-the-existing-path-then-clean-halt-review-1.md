## Code Review Summary

**Files Reviewed:** `orchestrator/agents.py` (`_classify_result` body + `_run_claude` tail). Cross-checked `main.py` (`except HaltError`), `tests/test_agents.py`, specs 31 & 33.
**Risk Level:** 🟢 Low

### Scope
Two code hunks: the `_classify_result` body (`agents.py:81-97`) and the rewired `_run_claude` terminal branch (`agents.py:268-299`). Read in full against the surrounding subprocess loop.

### Correctness — behavioral equivalence trace

The classifier + tail were traced row-by-row against the original inline logic (pre-change `agents.py:254-292`). Every non-network outcome is preserved; only the no-result nonzero exit is reclassified, which is the intended change.

- **Row 1 (overloaded/529, retry left)** → `"retry"` → prints the "API overloaded" line (`parsed_final` is populated, so the wording branch at `:271-274` selects the overloaded message). Identical to the old `retryable` gate. ✓
- **Rows 2–3 (no-result nonzero exit)** — the only new behavior. With retries left → `"retry"` → new "Network error / no result event" wording (`not parsed_final` true); exhausted → `"network_halt"` → `raise NetworkError(...)`, which subclasses `HaltError` and is caught by `cli()`'s `except HaltError` (`main.py:507-513`) → `HALTED` + `"stop"` alert + `sys.exit(0)`. This is exactly the reclassification specs 31/33 require. Previously this case fell to the `returncode != 0` → bare `RuntimeError`. ✓
- **Row 4 (nonzero + rate-limit substring)** → `"ratelimit"` → `RateLimitError(result_text)`. Original nonzero branch raised the same. ✓
- **Row 5 (nonzero, no rate-limit)** → `"error"` → `proc.returncode != 0` sub-branch → `RuntimeError("Claude CLI failed with exit code N\nstdout: ...")`. Byte-for-byte the original row-5 message. ✓
- **Rows 6–7 (`is_error`, returncode 0)** → `"ratelimit"` / `"error"`. For row 7 the `"error"` branch falls to the `else` → `RuntimeError(f"Claude returned error: {result_text[:500]}")` — the original row-7 message, and crucially not a false `"exit code 0"` string. This is the fix for plan-review-1's sole finding, and it is implemented correctly: the re-branch on `proc.returncode` preserves both first lines, including the one `cli()` forwards to Telegram (`str(e).splitlines()[0]`). ✓
- **Row 8 (ok)** → falls through to the empty-stdout guard then the success path. ✓

### Empty-stdout guard placement — verified safe
The guard (`if not lines: raise ...`, `agents.py:296-299`) now sits only on the `"ok"` path. The two cases where `lines` is empty:
- `lines` empty **and** returncode `!= 0`: `parsed_final == {}` → `no_result` true → routes to retry/`network_halt` (rows 2/3), never reaching the guard. Originally this raised the exit-code `RuntimeError`; the reroute to the network path is the intended behavior change.
- `lines` empty **and** returncode `== 0`: rows 1–7 all fail (empty `result_text`, `is_error` false, returncode 0) → `"ok"` → guard fires with the original `"Claude CLI exited 0 but stdout is empty"` message. Preserved. ✓

### Purity & constraints
- `_classify_result` is pure — no I/O, no `sleep`, no print, no guard folded in. Matches spec 33's explicit instruction. ✓
- No new constant, no backoff, no second attempt counter: the single `for attempt` loop and `MAX_RETRIES`/`RETRY_DELAY` are reused verbatim. ✓
- `NetworkError` type and the classifier tests (18.1.1) untouched; `main.py`/`notify.py` untouched. ✓

### Tests
`uv run pytest` → **187 passed**. The six previously-red `test_classify_result_*` assertions (`tests/test_agents.py:537-564`) now pass; no pre-existing test regressed. The `_run_claude` tail is a loud subprocess surface, correctly left to the reasoning-trace verify rather than a mock test, per spec 31.

### Findings
None.

REVIEW_PASS
