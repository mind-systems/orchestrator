# Code Review 2 (re-review): 21.1 — A result-bearing transport error is transient, not a verdict

**Previous review:** `.ai-factory/reviews/trickster77777/14-21-1-a-result-bearing-transport-error-is-transient-not-a-verdict-review-1.md`
**Files re-read in full at their current state:** `orchestrator/agents.py`, `tests/test_agents.py`; cross-checked against the task spec `41-transport-fault-is-not-a-verdict.md`, the plan, `docs/concepts/fault-handling.md`, and the exception's consumer `orchestrator/main.py:511-517`.

**Verdict:** 🟢 Pass. The single finding from review 1 is fixed; nothing new. `uv run pytest` green (**211 passed**). The delta since review 1 is exactly four docstring lines — no behavioural line changed, confirmed by `git diff HEAD -- orchestrator/ tests/`.

## Verdicts on review 1's findings

### Finding 1 — `agents.py:121-123`, the docstring's "always" is false for the very case this task fixes → **Fixed**

Current content, `orchestrator/agents.py:118-124`, quoted as it stands now:

```python
    Returns one of the literals `"retry" | "ratelimit" | "network_halt" |
    "error" | "ok"`. `no_result = not parsed_final` means the CLI exited
    before emitting any `result` event — an infra/network death, not a task
    outcome — as opposed to a result-bearing nonzero exit, which is a
    task-level outcome only when its text names no transport fault, or an
    `is_error` result on a zero exit, which is a task-level outcome
    whatever its text names.
```

The false clause "an `is_error` result, which is always a task-level outcome" is gone; the guarantee is now scoped to a **zero exit**, which is where it actually holds — the transport branches (`:131-133`) are gated on `returncode != 0` and cannot fire there. This matches the task spec's own narrower claim ("a marker with `returncode == 0` and `is_error` true still returns `"error"`").

Verified against the running code, not the text:

| Input | Result | Docstring now says |
|---|---|---|
| `is_error=True`, rc=1, transport marker, attempt 1/3 | `"retry"` | not covered by the `is_error` clause (nonzero exit) — correct |
| same, attempt 3/3 | `"network_halt"` | idem — correct |
| `is_error=True`, rc=0, `"connection reset"` | `"error"` | "a task-level outcome whatever its text names" — correct |

The flagship incident shape (`is_error: true` alongside exit 1 and the transport text) is now described accurately: it is a transport fault, not a verdict.

## Full re-review of the change

### Classification (`agents.py:92-147`)
- `_is_overloaded` (`:92-94`) is byte-equivalent to the expression it replaced; `_TRANSPORT_MARKERS` (`:97-104`) holds exactly the six pinned strings with no widening; `_is_transport_fault` (`:107-110`) is a case-insensitive substring test, no regex, no word boundaries.
- The two new branches (`:131-134`) sit directly after the overload branch and before the `no_result` pair — the pinned position — each carrying the load-bearing `returncode != 0` conjunct. The ratelimit branches (`:139-140`, `:143-144`), the `is_error` branch (`:145-146`), the markerless `"error"` branch (`:141-142`), and `MAX_RETRIES`/`RETRY_DELAY` are untouched. No new verdict literal.
- Table re-traced against the live function this pass: incident text at attempt 1/3 → `"retry"` (was `"error"` → bare `RuntimeError`, the defect); at 3/3 → `"network_halt"` → `NetworkError` → `except HaltError` → 🟡 clean `exit(0)`, resumable; `("boom", rc=1)` → `"error"`; `("You hit your limit", rc=1)` → `"ratelimit"`; `("handles connection reset", rc=0)` → `"ok"`; `parsed_final == {}` ⇒ `result_text == ""` ⇒ new branches provably inert, the `no_result` pair answers as before.

### Dispatch (`agents.py:328-347`)
- Retry print is the pinned three-way split — `not parsed_final`, then `_is_overloaded`, then transport — and is exhaustive by construction: a `"retry"` verdict can only originate in one of those three branches, so no retry path prints an unlabelled or wrong line, and text carrying both markers reports the overload, the reason the verdict was actually reached by.
- `network_halt` splits on `not parsed_final`, keeping the no-result message verbatim and raising `Claude CLI reported a transport failure, exit code {rc}` / `result: {result_text[:500]}` otherwise. First-line correctness re-confirmed against `main.py:515` (`str(e).splitlines()[0]`) — the operator gets the transport line, and it is a fixed literal, so an embedded newline in `result_text` cannot displace it. `[:500]` matches the cut at `:358`. Single `NetworkError`, no new exception type; control flow, verdict routing, and the `RETRY_DELAY` sleep unchanged.
- `NetworkError`'s docstring (`:158-161`) covers both routes.

### Tests (`tests/test_agents.py:540-600`)
Block header now reads `# The decision table: which terminal action a finished CLI invocation maps to.` — present tense, no plan-layer citation, and it no longer claims the cases are red against a stub. The six pre-existing cases are unchanged and pass; the five appended cases match the spec verbatim and their names state behaviour, not coordinates. No import, fixture, or assertion churn. Scope held: `git status` shows only `orchestrator/agents.py` and `tests/test_agents.py` modified alongside the plan/review artifacts.

No runtime hazard found: both predicates are pure functions over a `str` with no I/O, `result_text` is always a `str` (`parsed_final.get("result", "")`, `:323`), there is no new state, no on-disk format change, and therefore no migration and no resume implication — a `NetworkError` halt leaves the sidecar exactly as the existing no-result halt does.

## Deferred observations

- Affects: `orchestrator/agents.py:123-124` — the docstring's `is_error`-on-a-zero-exit clause says "a task-level outcome whatever its text names", but a zero-exit `is_error` result whose text names a rate limit returns `"ratelimit"` (`:143-144`), which is an operational halt, not a task-level outcome. The shorthand is inherited — the pre-task text made the same conflation ("an `is_error` result … are task-level outcomes") — and the ratelimit branches are explicitly out of this task's scope. Worth one clause whenever the ratelimit path is next touched.
- Affects: `orchestrator/agents.py:344-347` — the transport `NetworkError` carries `result: {result_text[:500]}` where the no-result branch carries the full `stdout`, and `_run_claude` does not echo the stream as it arrives (`:283-294` prints only the session line), so the raw event stream is not recoverable from the console on this path. Exactly what the spec pins, and the result text is the diagnostic for a transport fault; relevant only if a future fault needs the stream.
- Affects: `orchestrator/agents.py:139` — the ratelimit test matches the bare substring `"resets"` and the transport branches now precede it, so a hypothetical `"connection resets"` would classify as transport rather than rate limit. Both land on `HaltError`/🟡; carried from plan-review 1, relevant only if the ratelimit markers are tightened.

REVIEW_PASS
