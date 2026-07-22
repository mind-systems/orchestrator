# Network/retry classification contract — `_classify_result` seam + `NetworkError` + red tests

**Date:** 2026-07-22
**Source:** conversation context (skeleton/TDD split of task 18.1 — the classification is a silent-failure surface buried in a subprocess loop)

## Why this is a separate task

Task 18.1 changes how `_run_claude` (`agents.py:136`) treats a finished `claude` subprocess: a transient network death must be retried, then halted cleanly. That decision is a **5-way classification** (`retry` / `ratelimit` / `network_halt` / `error` / `ok`) whose errors are **silent** — a misclassified network death retries when it shouldn't, or crashes when it should retry, with no immediate signal (per the silent-failure discriminator, this is a "test" surface). Today the logic is inlined across `agents.py:229-258` and driven by a live `subprocess.Popen`, so it cannot be unit-tested. This task lays the **pure seam** the decision moves onto and pins its contract with **red tests**, before the impl task (18.1.2) fills the body and wires it in. Skeleton:impl is 1:1, so the skeleton and its red tests are fused into this one contract commit (compiles, tests red); 18.1.2 turns them green.

## Deliverable (compiles; tests red)

1. **The `NetworkError` type.** `class NetworkError(HaltError)` beside `RateLimitError` (`agents.py:73`). It subclasses `HaltError` so `cli()`'s `except HaltError` (`main.py:507-513`) later catches it as a clean `exit(0)` halt — no wiring yet, just the type.

2. **The `_classify_result` seam.** A pure function, no I/O, signature:

   ```python
   def _classify_result(parsed_final: dict, result_text: str, returncode: int,
                        is_error: bool, attempt: int, max_retries: int) -> str:
       ...  # body is 18.1.2's job — stub raises NotImplementedError here
   ```

   Returns one of the string literals `"retry" | "ratelimit" | "network_halt" | "error" | "ok"`. In this task the body is a stub (`raise NotImplementedError`) — it exists to be imported and tested, not to run. `_run_claude` is **not** rewired here (its inline logic still drives the live path until 18.1.2).

3. **Red tests** in `tests/test_agents.py` pinning the decision contract below. They import and call `_classify_result` directly (no subprocess), so they compile and run **red** against the stub.

## The decision contract (what 18.1.2 must satisfy)

`no_result = not parsed_final` — the CLI exited before emitting any `result` event (infra/network, not a task outcome). Precedence, top to bottom (mirrors the current inline flow at `agents.py:233-258`, with the network row added):

| # | Condition | Result |
|---|---|---|
| 1 | (`"overloaded"` in `result_text.lower()` or `"529"` in `result_text`) and `attempt < max_retries` | `"retry"` |
| 2 | `no_result` and `returncode != 0` and `attempt < max_retries` | `"retry"` |
| 3 | `no_result` and `returncode != 0` (retries exhausted) | `"network_halt"` |
| 4 | `returncode != 0` and (`"hit your limit"` or `"resets"` in `result_text.lower()`) | `"ratelimit"` |
| 5 | `returncode != 0` | `"error"` |
| 6 | `is_error` and (`"hit your limit"` or `"resets"` in `result_text.lower()`) | `"ratelimit"` |
| 7 | `is_error` | `"error"` |
| 8 | otherwise | `"ok"` |

The empty-stdout guard (`if not lines: raise` at `agents.py:250-253`) stays **inline** in `_run_claude` — it is a stdout-vs-parsed concern, out of this classifier's inputs; do not fold it in.

## Tests (red)

`tests/test_agents.py`, one assertion per contract row, calling `_classify_result` directly:

- network death, retry left: `{}`, `""`, `returncode=1`, `is_error=False`, `attempt=1`, `max_retries=3` → `"retry"` (row 2).
- network death, exhausted: same but `attempt=3` → `"network_halt"` (row 3).
- overloaded, retry left: `result_text="overloaded"`, `attempt=1` → `"retry"` (row 1).
- real CLI error: `{"result":"boom"}`, `result_text="boom"`, `returncode=1`, `attempt=3` → `"error"` (row 5).
- rate limit: `result_text="You hit your limit"`, `returncode=1` → `"ratelimit"` (row 4).
- clean success: `{"result":"done","is_error":False}`, `returncode=0` → `"ok"` (row 8).

These are pure silent-failure assertions (a wrong classification silently changes the run's terminal outcome). Loud surfaces — the `NetworkError` subclassing (a wrong base class fails at `except HaltError` wiring time, caught by 18.1.2's run) — get no test.

## Verify

- `uv run pytest` compiles and runs; the `_classify_result` tests are **red** (stub raises), every pre-existing test stays **green** (nothing rewired).
- `NetworkError` importable and `issubclass(NetworkError, HaltError)` holds.

## What NOT to do

- Do **not** implement the `_classify_result` body or rewire `_run_claude` — that is 18.1.2. This task ships a stub + red tests only.
- Do **not** fold the empty-stdout guard or the retry `time.sleep`/`continue` mechanics into the classifier — it decides, it does not act.
- Do **not** change `MAX_RETRIES`/`RETRY_DELAY` or add backoff.
- Touch `agents.py` (type + seam) and `tests/test_agents.py` only.
