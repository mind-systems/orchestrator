# Code Review: 21.1 — A result-bearing transport error is transient, not a verdict

**Files reviewed:** `orchestrator/agents.py`, `tests/test_agents.py` (both read in full around the changed regions and their callers), cross-checked against the task spec `.ai-factory/specs/trickster77777/41-transport-fault-is-not-a-verdict.md`, the plan, the governing spec `docs/concepts/fault-handling.md`, and the consumer of the raised exception (`orchestrator/main.py:511-517`).

**Verdict:** 🟡 One finding — documentation-only, inside the changed lines. Behaviour is correct and matches the spec branch-for-branch; `uv run pytest` green (**211 passed**). No security, resume-safety, or data issue.

## What was verified

### Classification (`agents.py:92-146`)
- `_is_overloaded` (`:92-94`) reproduces the old inline expression byte-for-byte (`"overloaded" in result_text.lower() or "529" in result_text`) — a pure extraction, no behaviour change. `test_classify_result_overloaded_retry_left` still drives it through the classifier.
- `_TRANSPORT_MARKERS` (`:97-104`) holds exactly the six pinned strings, no widening; `_is_transport_fault` (`:107-110`) is a case-insensitive substring test with no regex and no word-boundary logic, matching the existing style.
- The two new branches (`:130-133`) sit **directly after** the overload branch and **before** the `no_result` pair, exactly the pinned position, each carrying the load-bearing `returncode != 0` conjunct. No other branch moved, changed a conjunct, or changed a return literal; no new verdict literal was introduced. `MAX_RETRIES`/`RETRY_DELAY` untouched.

Full-table trace of the new order:

| Input | Verdict | Note |
|---|---|---|
| `"API Error: Connection closed mid-response."`, rc=1, attempt 1/3 | `"retry"` | the incident — was `"error"` → bare `RuntimeError` on the first attempt |
| same, attempt 3/3 | `"network_halt"` | → `NetworkError` → `except HaltError` → 🟡 clean exit(0), resumable |
| `"boom"`, rc=1 | `"error"` | markerless nonzero exit unaffected |
| `"You hit your limit"`, rc=1 | `"ratelimit"` | unaffected |
| `"handles connection reset"`, rc=0 | `"ok"` | marker in a *successful* result is inert — the naive-fix failure mode, closed |
| `parsed_final == {}` (⇒ `result_text == ""`), rc=1 | `"retry"`/`"network_halt"` via the `no_result` pair | new branches provably inert: no marker is a substring of `""` |

### Dispatch strings (`agents.py:327-346`)
- The retry print is a three-way split in the pinned order — `not parsed_final`, then `_is_overloaded`, then transport. **Exhaustive by construction:** a `"retry"` verdict can only originate in the overload branch, the `no_result` branch, or the transport branch, so no retry path prints an unlabelled or wrong line. Text carrying both an overload and a transport marker reports the overload — the reason the verdict was actually reached by.
- The `network_halt` raise splits on `not parsed_final`, keeping the existing no-result message verbatim and adding `Claude CLI reported a transport failure, exit code {rc}` / `result: {result_text[:500]}`. First-line correctness confirmed against `main.py:515` (`str(e).splitlines()[0]`): the operator now receives the transport line, not "died with no result event". The `[:500]` cut matches `:357`. Still a single `NetworkError`; no new exception type. Control flow, verdict routing, and the `RETRY_DELAY` sleep are untouched.
- `NetworkError`'s docstring (`:157-160`) now covers both routes.

### Tests (`tests/test_agents.py:540-600`)
The stale block header ("Red against the `NotImplementedError` stub … a follow-up task fills in") is replaced by a present-tense, plan-layer-free line — the plan-review finding is closed, with no assertion, name, import, or fixture touched, and the `# Task N:` citations elsewhere in the file left as deliberate evidence. The five appended cases match the spec verbatim; the six pre-existing cases are unchanged and pass. Scope held: only `agents.py` and `tests/test_agents.py` are modified. No doc change was owed — `fault-handling.md` already leads with this behaviour.

## Findings

### 1. `agents.py:121-123` — the docstring's "always" is false for the very case this task fixes

The reworded clause reads:

> …as opposed to a result-bearing nonzero exit, which is a task-level outcome only when its text names no transport fault, or an `is_error` result, **which is always a task-level outcome**.

The first half is correct. The second is not, because the new transport branches (`:130-133`) sit **ahead** of the `is_error` branches (`:142-145`) and are gated only on `returncode != 0` — not on `is_error`. So:

```python
_classify_result({"result": "API Error: Connection closed mid-response.", "is_error": True},
                 "API Error: Connection closed mid-response.", 1, True, 1, 3)   # -> "retry"
```

An `is_error` result is therefore *not* always a task-level outcome: with a nonzero exit and a transport marker it classifies as transport, which is precisely the intended behaviour and precisely the shape of the incident this task exists for — the CLI's `result` event for an API error normally carries `is_error: true` alongside exit 1. The docstring, read literally, tells the next maintainer that this input is a task-level outcome, i.e. the belief this task was written to overturn.

The task spec's own claim is narrower and correct: *"a marker with `returncode == 0` and `is_error` true still returns `"error"`"* — the `is_error` guarantee holds on a **zero** exit, where the transport branches cannot fire.

**Suggested fix** — one clause, no code change:

```
    outcome — as opposed to a result-bearing nonzero exit, which is a
    task-level outcome only when its text names no transport fault, or an
    `is_error` result on a zero exit, which is a task-level outcome
    whatever its text names.
```

Nothing else in the docstring needs touching, and no test asserts this wording.

## Deferred observations

- Affects: `orchestrator/agents.py:343-346` — the transport `NetworkError` carries `result: {result_text[:500]}` where the no-result branch carries the full `stdout`. Since `_run_claude` does not echo the stream as it arrives (only `[session: …]` lines are printed, `:282-293`), the raw event stream is not recoverable from the console on this path — only the 500-char result text is. This is exactly what the task spec pins, and the result text *is* the diagnostic for a transport fault, so it is right for this task; it is worth knowing only if a future fault needs the stream to diagnose.
- Affects: `orchestrator/agents.py:138` — the ratelimit test matches the bare substring `"resets"`, and the transport branches now precede it, so a hypothetical text reading `"connection resets"` would classify as transport rather than rate limit. Both land on `HaltError`/🟡 and no observed message has this shape; carried over from plan-review-1, still only relevant if the ratelimit markers are ever tightened.
