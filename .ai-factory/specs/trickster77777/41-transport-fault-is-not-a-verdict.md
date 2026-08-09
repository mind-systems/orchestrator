# A result-bearing transport error is transient, not a verdict

**Date:** 2026-08-09
**Source:** conversation context (incident post-mortem: a network drop during plan review reported `API Error: Connection closed mid-response.` with exit 1 and tore down a multi-hour run with a traceback)

## Problem today

`_classify_result` (`agents.py:92-120`) treats the mere presence of a `result` event as proof the agent reached a verdict about the work — `no_result = not parsed_final` (`:104`) is the only gate that recognizes an unanswered call, and it is `False` whenever the CLI emits *any* `result` event, however that event got there. When the CLI dies mid-response and the last line of its stream carries `{"result": "API Error: Connection closed mid-response.", ...}` with exit code `1`:

- `no_result` is `False` — a `result` key exists;
- neither `"overloaded"` nor `"529"` is in the text, so the first branch (`:106`) does not match;
- both `no_result`-gated branches (`:108`, `:110`) are skipped;
- `"hit your limit"`/`"resets"` is absent, so the ratelimit branch (`:112`) does not match;
- `returncode != 0` (`:114`) matches — the function returns `"error"`.

`_run_claude` (`:317-323`) turns `"error"` into a bare `RuntimeError`, raised on the **first** attempt with zero retries. Nothing between there and `cli()` catches a bare `RuntimeError`; it reaches the generic `except Exception` (`main.py:525-531`), which notifies and re-raises — an unhandled traceback tears down the run. A transport failure reported through the `result` channel is indistinguishable, at this seam, from a genuine task-level error such as a broken session id or an unrecognized flag — both return `"error"` today.

## The change

The classifier's existing overload test gets a name, `_is_overloaded`, and gains a sibling, `_is_transport_fault`, recognizing a transport fault inside `result_text`. Two new branches answer it exactly as the `no_result` pair answers a silent death — retry while attempts remain, halt cleanly once they are spent:

```python
def _is_overloaded(result_text: str) -> bool:
    """True if result_text names an API overload."""
    return "overloaded" in result_text.lower() or "529" in result_text


_TRANSPORT_MARKERS = (
    "connection closed mid-response",
    "connection error",
    "connection reset",
    "econnreset",
    "fetch failed",
    "socket hang up",
)


def _is_transport_fault(result_text: str) -> bool:
    """True if result_text names a transport failure, case-insensitively, as a substring."""
    lowered = result_text.lower()
    return any(marker in lowered for marker in _TRANSPORT_MARKERS)
```

`_classify_result`'s existing overload branch (`agents.py:106`) calls `_is_overloaded(result_text)` in place of its inline expression — the branch's only change; its position, its `attempt < max_retries` conjunct, and its `"retry"` return are untouched.

Two new branches in `_classify_result`, inserted directly after the existing `overloaded`/`529` branch (`:106-107`) and before the `no_result` pair (`:108-111`):

```python
    if _is_transport_fault(result_text) and returncode != 0 and attempt < max_retries:
        return "retry"
    if _is_transport_fault(result_text) and returncode != 0:
        return "network_halt"
```

The two are disjoint from the `no_result` pair by construction: a no-result death carries `parsed_final == {}`, hence `result_text == ""`, and `_is_transport_fault("")` is always `False` (no marker is a substring of the empty string). Both new branches carry `returncode != 0`, which is what makes their precedence match rows 2 and 3 of the existing table exactly — attempts-remaining wins over exhaustion, and both sit ahead of the ratelimit/error/is_error branches below them, so a transport-marked text never falls through to `"error"`.

The `returncode != 0` conjunct is load-bearing, not decorative: `result_text` is the agent's own final message (`parsed_final.get("result", "")`, `agents.py:295`), not a transport-layer error string, so a *successful* run can still name a transport failure in its own prose — a plan or a review written about this very task, for instance. Without the conjunct, that text would reclassify as `"retry"`, re-running a multi-hour step and silently accepting whatever a later attempt happens to produce instead. A marker inside a successful result (`returncode == 0`) is therefore inert and classifies exactly as it does today; a marker with `returncode == 0` and `is_error` true still returns `"error"`, because `is_error` marks a task-level outcome by this function's own contract and a transport fault is not one — collapsing the two would erase the distinction this task exists to draw.

`_run_claude`'s call site (`:298-341`) keeps its control flow and verdict routing exactly as it is: the new branches reach the existing `"retry"`/`"network_halt"` handling (`:300-312`) by a second route, unchanged. Two operator-facing strings inside that handling gain a transport case, because both currently hardcode the assumption that only an overload or a no-result death can arrive there:

- **The retry print (`agents.py:301-304`).** Today it is a two-way split on `not parsed_final`, so a result-bearing transport retry falls to the `else` and prints "API overloaded" for a connection drop. It becomes a three-way split, in this order: `not parsed_final` first (a no-result death carries no markers, so it is unambiguous), then `_is_overloaded(result_text)` — ahead of the transport test, mirroring the classifier's own branch order, so a text carrying both markers reports the reason the verdict was actually reached by — and the transport case last, printing `>>> Transport error, retrying in {RETRY_DELAY}s (attempt {attempt}/{MAX_RETRIES})...`, matching the shape of the two existing lines.
- **The `NetworkError` message (`agents.py:308-312`).** Today it opens "Claude CLI died with no result event", which is false for the new route. It splits on `not parsed_final`: the existing text for the no-result route, a transport text otherwise — first line `Claude CLI reported a transport failure, exit code {proc.returncode}`, second line `result: {result_text[:500]}` (matching the existing `[:500]` cut at `:323`). The first line is load-bearing: `main.py:511-516` takes `str(e).splitlines()[0]` and sends exactly that line to the operator, so a wrong first line is the wrong report delivered.

**Two docstrings state the premise this task overturns; both correct in the same move:**

- `_classify_result`'s docstring (`agents.py:94-101`) ends "…as opposed to a result-bearing nonzero exit or an `is_error` result, which are task-level outcomes." After this task a result-bearing nonzero exit is a task-level outcome only when its text names no transport fault; reword that clause to say so. The sentence describing the return literals and `no_result` stays as it is.
- `NetworkError`'s docstring (`agents.py:131-133`) says the CLI "dies before emitting any `result` event." It covers both routes after this task: a death before any `result` event, and a `result` event whose text names a transport fault — in both cases with retries exhausted.

## Supersedes

`31-network-cli-death-retry-then-halt.md`'s "What NOT to do" pinned: *"Do **not** reclassify a nonzero exit that emitted a `result` event, nor the `is_error` path — those are real errors; only the no-result death becomes retryable/haltable."* This task overrides that clause. Its premise no longer holds: at the time it was written, no `result`-bearing text had been observed as a transport failure, so treating every result-bearing nonzero exit as a real error was the safe default. The incident this task fixes is exactly a `result`-bearing transport failure — the assumption that a `result` event always carries a genuine answer was the defect, not the classification built on it. The ratelimit branch, the `is_error` branches, and a markerless nonzero exit (a broken session id, a missing file, an unrecognized flag) are unaffected and keep returning `"ratelimit"`/`"error"` exactly as today.

## Guards

- The overload route, the ratelimit routes, and the `is_error` routes keep their behaviour, their position, and their return literals exactly as they are. Substituting `_is_overloaded(result_text)` for the overload branch's inline expression is not a behaviour change and is the only edit any of them takes. The two new branches go in the stated position and nowhere else.
- Do not change `MAX_RETRIES`/`RETRY_DELAY` (`:39-40`) — this task is classification only; retry timing is out of scope for this roadmap.
- `_run_claude`'s dispatch (`:298-341`): its control flow, its verdict routing, and the `RETRY_DELAY` sleep stay exactly as they are. The only changes inside it are the two operator-facing strings named in `## The change` — the retry print and the `NetworkError` message. No new verdict literal is introduced.
- `_TRANSPORT_MARKERS` is matched case-insensitively as a substring — no regex, no word-boundary logic, mirroring the existing `"overloaded"`/`"529"` check's own substring style.

## Tests

`tests/test_agents.py`, appended to the `# --- _classify_result ---` block (`:541-577`), one-line-assert style matching the existing six cases:

```python
def test_classify_result_transport_fault_retry_left():
    """A result-bearing transport error retries while attempts remain."""
    assert _classify_result({"result": "API Error: Connection closed mid-response."}, "API Error: Connection closed mid-response.", 1, False, 1, 3) == "retry"


def test_classify_result_transport_fault_exhausted():
    """A result-bearing transport error halts once attempts are spent."""
    assert _classify_result({"result": "API Error: Connection closed mid-response."}, "API Error: Connection closed mid-response.", 1, False, 3, 3) == "network_halt"


def test_classify_result_markerless_nonzero_still_errors():
    """A nonzero exit with no transport marker keeps classifying as a task-level error."""
    assert _classify_result({"result": "boom"}, "boom", 1, False, 1, 3) == "error"


def test_classify_result_ratelimit_text_still_ratelimit():
    """Rate-limit text is unaffected by the new transport branches."""
    assert _classify_result({"result": "You hit your limit"}, "You hit your limit", 1, False, 1, 3) == "ratelimit"


def test_classify_result_transport_marker_in_successful_result_is_inert():
    """A transport marker inside a successful result text is not a transport fault."""
    assert _classify_result({"result": "handles connection reset", "is_error": False}, "handles connection reset", 0, False, 1, 3) == "ok"
```

Extracting `_is_overloaded` takes no new case: it is behaviour-preserving, and `test_classify_result_overloaded_retry_left` already exercises the predicate through the classifier.

## Verify

- `uv run pytest` green, including the five new cases above and all six pre-existing `_classify_result` cases unchanged.
- Manual trace over the incident text (`"API Error: Connection closed mid-response."`, exit `1`, attempt 1 of 3): now returns `"retry"`, not `"error"` — the run survives the first hit instead of dying immediately.
- Manual trace over the same text through `_run_claude`'s dispatch: with retries remaining, the console prints the transport line, not "API overloaded"; once retries are spent, the raised `NetworkError`'s first line names a transport failure with the exit code, not "no result event" — that first line is what reaches the operator. The two strings are verified by this trace, not by a test: asserting them would mean driving the CLI itself.

## What NOT to do

- Do not add a new exception type — `NetworkError` already exists and already covers `"network_halt"`.
- Do not widen `_TRANSPORT_MARKERS` beyond the six pinned strings without a new observed case; a guess adds surface without evidence.
- Touch `agents.py` and `tests/test_agents.py` only.
