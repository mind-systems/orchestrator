# Plan: 18.1.2 — Network-caused CLI death: retry on the existing path, then clean halt

## Context
Fill the pure `_classify_result` body (seam laid in 18.1.1) per its 8-row decision table, then rewire `_run_claude`'s terminal tail to branch on the classifier so a no-`result` network death retries on the existing 529 path and, once exhausted, raises `NetworkError(HaltError)` for a clean `exit(0)` + resume instead of a raw traceback.

## Settings
- Testing: no (18.1.1's red tests go green; add none)
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Fill the classifier

- [x] **Task 1: Implement `_classify_result` body per the decision table**
  Files: `orchestrator/orchestrator/agents.py`
  Replace the `raise NotImplementedError` stub body (`agents.py:69-83`) with the 8-row decision, evaluated top-to-bottom with the same precedence and the same substring checks the current inline tail uses. Compute `no_result = not parsed_final` once at the top. Then, in order:
  1. `("overloaded" in result_text.lower() or "529" in result_text) and attempt < max_retries` → `"retry"`
  2. `no_result and returncode != 0 and attempt < max_retries` → `"retry"`
  3. `no_result and returncode != 0` (retries exhausted) → `"network_halt"`
  4. `returncode != 0 and ("hit your limit" in result_text.lower() or "resets" in result_text.lower())` → `"ratelimit"`
  5. `returncode != 0` → `"error"`
  6. `is_error and ("hit your limit" in result_text.lower() or "resets" in result_text.lower())` → `"ratelimit"`
  7. `is_error` → `"error"`
  8. otherwise → `"ok"`
  Keep it pure — no I/O, no `time.sleep`, no printing; the function decides, it does not act (the empty-stdout guard stays out of it). Match the exact `.lower()`/substring forms already in `_run_claude` so the reasoning trace and the existing behavior for the 529 / ratelimit / error / ok rows is byte-for-byte identical. This turns the six red assertions in `tests/test_agents.py` (`test_classify_result_*`, lines 537-564) green.

### Phase 2: Rewire `_run_claude`'s tail

- [x] **Task 2: Drive `_run_claude`'s terminal branch off the classifier** (depends on Task 1)
  Files: `orchestrator/orchestrator/agents.py`
  Rewire the tail at `agents.py:254-292`. After `result_text`/`is_error` are extracted (`agents.py:251-252`), replace the inline `retryable` gate + `if proc.returncode != 0` block + `is_error` block with a single call:
  `verdict = _classify_result(parsed_final, result_text, proc.returncode, is_error, attempt, MAX_RETRIES)`
  then branch on `verdict`:
  - `"retry"` → reuse the existing retry block verbatim (`time.sleep(RETRY_DELAY)`, `continue`), but branch the printed wording: when `not parsed_final` print a network-blip retry line (e.g. `">>> Network error / no result event, retrying in {RETRY_DELAY}s (attempt {attempt}/{MAX_RETRIES})..."`), otherwise keep the existing `">>> API overloaded, retrying in {RETRY_DELAY}s ..."` line. No new constant, no backoff, no second attempt counter — `MAX_RETRIES`/`RETRY_DELAY` and the same `for attempt` loop only.
  - `"network_halt"` → `raise NetworkError(...)` with a short message plus the captured `stdout` (e.g. the exit code and `stdout: {stdout if stdout else '(empty)'}`), mirroring the existing error message shape.
  - `"ratelimit"` → `raise RateLimitError(result_text)` (unchanged behavior).
  - `"error"` → preserve **both** original error messages, which the single verdict collapses. Re-branch on the raw inputs still in scope: if `proc.returncode != 0`, `raise RuntimeError(f"Claude CLI failed with exit code {proc.returncode}\nstdout: {stdout if stdout else '(empty)'}")` (the row-5 message, `agents.py:267-270`); otherwise (the `is_error`-with-clean-exit-0 case, row 7) `raise RuntimeError(f"Claude returned error: {result_text[:500]}")` (the row-7 message, `agents.py:280`). This keeps both first lines byte-for-byte — including the one `cli()` forwards to the Telegram alert (`str(e).splitlines()[0]`, `main.py:511`) — so the `is_error`/exit-0 path stays truly unchanged rather than emitting a false `"exit code 0"` string.
  - `"ok"` → fall through to the existing success path.
  Keep the empty-stdout guard (`if not lines: raise RuntimeError("Claude CLI exited 0 but stdout is empty")`, `agents.py:272-275`) inline on the `"ok"` path — it is not the classifier's concern; it must still guard before the session-id / summary / `return`. Leave the trailing `raise RuntimeError("All retry attempts exhausted")` (`agents.py:292`) as the loop's final backstop. Do not touch `cli()`'s `except HaltError` block in `main.py` — `NetworkError` flows through it by subclassing `HaltError`. Do not touch `notify.py`. Do not edit or re-add the `NetworkError` type or the classifier tests (landed in 18.1.1).
