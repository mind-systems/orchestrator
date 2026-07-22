# Network-caused CLI death: retry on the existing path, then clean halt

**Date:** 2026-07-22
**Source:** conversation context (post-mortem of a real 2h run that died mid-review on a network drop)

## Problem today

`_run_claude` (`agents.py:136`) classifies a finished `claude` subprocess by scanning its `stream-json` output for the last event carrying a `result` key (`agents.py:216-230`). When the CLI dies from a **transient network / DNS loss**, it prints the opening `init` system event and then exits nonzero **without ever emitting a `result` event**. So:

- `parsed_final = {}` → `result_text = ""`, `is_error = False`;
- the retry gate `retryable = ("overloaded" in result_text.lower() or "529" in result_text) and attempt < MAX_RETRIES` (`agents.py:233-235`) is **False** (empty `result_text` matches neither substring);
- execution falls to `agents.py:242-248`: `proc.returncode != 0`, and `result_text` holds no `"hit your limit"`/`"resets"`, so it raises a **bare `RuntimeError`**.

That `RuntimeError` is not a `HaltError`, so nothing on the way up catches it gracefully: it propagates through `review()` → `process_task()` → the dynamic loop → `cli()`'s `except Exception` (`main.py:514-520`), which fires a "stop" Telegram alert (itself failing on the same dead DNS) and re-`raise`s → a full traceback tears down a multi-hour run.

Real incident: a code review at iteration 3 died exactly this way after the run had been going 2h 3m. The tell was a **correlated** Telegram failure at the same instant — `<urlopen error [Errno 8] nodename nor servname provided, or not known>` (a `getaddrinfo`/DNS failure) — proving the host had lost name resolution, i.e. a network drop, not a task defect or a real CLI error.

Two things are wrong:
1. A transient network blip — which self-heals in seconds — is treated as fatal instead of retryable, even though the retry machinery for the sibling transient class (overloaded / 529) already exists right here.
2. When the network is down for good, the run dies with a raw traceback instead of the clean, resumable operational halt the orchestrator already has a path for (`HaltError` → `cli()` `except HaltError` → `sys.exit(0)`).

## The fix

**Depends on 18.1.1** (spec `33-network-classifier-contract-red-tests.md`): the `NetworkError(HaltError)` type and the pure `_classify_result` seam — with its decision table and red tests — already exist on disk. This task (18.1.2) fills the classifier body and rewires `_run_claude` to drive off it. One file (`agents.py`), reusing the current retry mechanism verbatim; do **not** add a second retry branch, a new attempt counter, or exponential backoff (owner decision: identical logic to the 529 path — `MAX_RETRIES = 3` so two extra attempts, fixed `RETRY_DELAY = 30`s, `agents.py:39-40`).

**1 — Fill `_classify_result`.** Implement the body per the decision table in spec 33 (rows 1-8, precedence top-to-bottom), returning `"retry" | "ratelimit" | "network_halt" | "error" | "ok"`. The `no_result = not parsed_final` row is what folds the no-result network death into the retryable/haltable set. Filling the body turns 18.1.1's red tests green.

**2 — Rewire `_run_claude`'s tail** (`agents.py:229-258`) to call the classifier once per finished attempt and branch on its verdict:
- `"retry"` → the existing retry block (`agents.py:237-240`): print the retry line (branch the wording for the network case vs "API overloaded"), `time.sleep(RETRY_DELAY)`, `continue`;
- `"network_halt"` → `raise NetworkError(...)` with a short message plus the captured `stdout`;
- `"ratelimit"` → `raise RateLimitError(result_text)` (unchanged);
- `"error"` → `raise RuntimeError(...)` with the `stdout` (unchanged);
- `"ok"` → fall through to the existing success path (session id, summary, `return`).

The empty-stdout guard (`agents.py:250-253`) stays inline around the `"ok"` path — it is not the classifier's concern.

Because `NetworkError` subclasses `HaltError`, `cli()`'s `except HaltError` (`main.py:507-513`) catches the exhausted-network case → prints `HALTED`, sends the `"stop"` alert, `sys.exit(0)` — a clean operational halt, resumable from the sidecar (the task never marked done), no traceback. A nonzero exit that **did** emit a `result` event (a real CLI/argument error, or an `is_error` result) classifies as `"error"`/`"ratelimit"` and keeps its current handling. Only the no-result case is reclassified.

## Behavior after the fix

- **Transient blip** (network returns within a retry window): the review/plan/implement call retries up to twice at 30s and continues — the multi-hour run survives instead of dying and needing a manual restart. This is the common case.
- **Network down for good**: after the retries are exhausted, `NetworkError` → clean `HALTED` + `"stop"` alert + `exit(0)`; on the next launch the sidecar resume picks the task back up. `notify`'s own DNS failure is already swallowed (`send_telegram`'s `try/except` in `notify.py`), so the halt path itself never crashes.
- **Overloaded / 529**: unchanged — same branch, same messages.
- **Real CLI/arg error (nonzero exit *with* a result event) or `is_error`**: unchanged — still surfaces as `RuntimeError`/`RateLimitError`.

## Tests

The classification contract and its red unit tests are task 18.1.1 (spec 33) — they already sit in `tests/test_agents.py`, red against the stub. This task implements `_classify_result` so those tests go **green**; it adds no new unit tests. The rewiring of `_run_claude` is exercised by the reasoning trace in Verify, not by a subprocess-mocking test (the live-process path is a loud surface — a wiring error throws at run time).

## Verify

- `uv run pytest` green — the `_classify_result` cases authored red in 18.1.1 now pass, and no pre-existing test regresses.
- Manual reasoning trace over the incident: an `init`-only, nonzero-exit stream now retries twice then raises `NetworkError`, and `cli()` exits 0 with `HALTED` — no traceback.

## What NOT to do

- Do **not** add exponential backoff, a new retry-count constant, or a separate retry loop — reuse `MAX_RETRIES` / `RETRY_DELAY` and the existing block (explicit owner decision: same logic as 529).
- Do **not** reclassify a nonzero exit that emitted a `result` event, nor the `is_error` path — those are real errors; only the no-result death becomes retryable/haltable.
- Do **not** retry the exit-0-empty-stdout guard (`agents.py:250-253`) — leave it as-is.
- Do **not** touch `notify.py` — its DNS failure is already caught and printed; the halt path relies on that.
- Touch `agents.py` only — the `NetworkError` type and the `_classify_result` tests already landed in 18.1.1; do not re-add or edit them here (fill the body and wire the call site). Do not alter `cli()`'s `except HaltError` block — `NetworkError` flows through it by subclassing.
