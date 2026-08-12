# Plan: 21.1 — A result-bearing transport error is transient, not a verdict

## Context
A transport failure that arrives *carrying its own error text* (`{"result": "API Error: Connection closed mid-response.", ...}` with exit 1) currently falls through `_classify_result`'s `returncode != 0` branch to `"error"` and dies as a bare `RuntimeError` on the first attempt, tearing down a multi-hour run. Teach the classifier a transport-marker predicate over `result_text` and two branches mirroring the `no_result` pair — retry while attempts remain, `NetworkError` once spent — and give the two operator-facing strings on that path a transport case so the drop is reported as what it was.

## Settings
- Testing: no — the five cases pinned by the task spec only, no coverage beyond them
- Logging: minimal
- Docs: no

## Ground-truth notes (read before implementing)
- **Task spec (the full contract):** `.ai-factory/specs/trickster77777/41-transport-fault-is-not-a-verdict.md` — every code sketch, marker string, branch position, and guard below comes from it verbatim; read it before editing.
- **Governing spec of the phase:** [`docs/concepts/fault-handling.md`](../../../docs/concepts/fault-handling.md) — already states present-tense that "a transport failure that arrives carrying its own error text" is "handled identically to a transport failure that arrives with no answer at all", and Invariant 1 "a transport failure is never a verdict". The doc leads and already matches the target: **no doc change is part of this task.**
- **Supersession:** this task overrides `31-network-cli-death-retry-then-halt.md`'s "What NOT to do" pin ("do not reclassify a nonzero exit that emitted a `result` event"). Only that clause; the ratelimit branches, the `is_error` branches, and a markerless nonzero exit are unaffected.
- **Verified ground truth in `agents.py` (current line numbers):** `_classify_result` at `:92-120` (overload branch `:106`, `no_result` pair `:108-111`, ratelimit `:112`, `returncode != 0 → "error"` `:114`); `NetworkError` at `:131-133`; `_run_claude`'s dispatch at `:298-341` (retry print `:300-306`, `network_halt` raise `:308-312`, the `[:500]` cut at `:323`).
- **Why the first line of the `NetworkError` message is load-bearing:** `main.py:511-516` takes `str(e).splitlines()[0]` and sends exactly that one line to the operator — a wrong first line is the wrong report delivered.
- **Touch `orchestrator/agents.py` and `tests/test_agents.py` only.**

## Tasks

### Phase 1: The classifier learns a transport fault

- [x] **Task 1: Name the overload test, add the transport predicate**
  Files: `orchestrator/agents.py`
  Add two module-level helpers immediately above `_classify_result` (i.e. after `_write_session`, `:80-89`), exactly as pinned by the task spec:
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
  `_is_overloaded` reproduces the existing inline expression at `:106` byte-for-byte in behaviour — extraction only. Do **not** widen `_TRANSPORT_MARKERS` beyond these six strings; matching is case-insensitive substring, no regex and no word-boundary logic, mirroring the existing `"overloaded"`/`"529"` style.

- [x] **Task 2: Two branches — retry while attempts remain, halt once spent** (depends on Task 1)
  Files: `orchestrator/agents.py`
  In `_classify_result` (`:104-120`):
  1. Replace the overload branch's inline expression (`:106`) with `_is_overloaded(result_text)`. Its position, its `and attempt < max_retries` conjunct, and its `return "retry"` are untouched — this is the branch's only change.
  2. Insert the two new branches **directly after** that overload branch (`:106-107`) and **before** the `no_result` pair (`:108-111`):
     ```python
     if _is_transport_fault(result_text) and returncode != 0 and attempt < max_retries:
         return "retry"
     if _is_transport_fault(result_text) and returncode != 0:
         return "network_halt"
     ```
     The `returncode != 0` conjunct is load-bearing, not decorative: `result_text` is the agent's own final message (`parsed_final.get("result", "")`, `:295`), so a *successful* run may name a transport failure in its own prose — a plan or a review written about this very task. Without the conjunct such text would reclassify as `"retry"`, silently re-running a multi-hour step. A marker inside a `returncode == 0` result stays inert and classifies exactly as today, including the `is_error` route: `is_error` marks a task-level outcome by this function's own contract, and a transport fault is not one.
  3. Reword the docstring's closing clause (`:99-101`). Today it reads "…as opposed to a result-bearing nonzero exit or an `is_error` result, which are task-level outcomes"; a result-bearing nonzero exit is now a task-level outcome **only when its text names no transport fault** — say that. Leave the sentence describing the return literals and `no_result` as it is.
  No other branch moves, changes its conjuncts, or changes its return literal; no new verdict literal is introduced. The new pair is disjoint from the `no_result` pair by construction — a no-result death carries `parsed_final == {}`, hence `result_text == ""`, and no marker is a substring of the empty string.

### Phase 2: The run gets words for what it survived

- [x] **Task 3: The retry line and the `NetworkError` message gain a transport case** (depends on Task 2)
  Files: `orchestrator/agents.py`
  Inside `_run_claude`'s dispatch (`:298-341`), change **only** the two operator-facing strings. Control flow, verdict routing, the `RETRY_DELAY` sleep, `MAX_RETRIES`/`RETRY_DELAY` (`:39-40`), and every other raise stay exactly as they are.
  1. **The retry print (`:301-304`)** — today a two-way split on `not parsed_final`, so a result-bearing transport retry falls to the `else` and prints "API overloaded" for a connection drop. Make it a three-way split in this order: `not parsed_final` first (a no-result death carries no markers, so it is unambiguous), then `_is_overloaded(result_text)` — ahead of the transport test, mirroring the classifier's own branch order, so text carrying both markers reports the reason the verdict was actually reached by — then the transport case, printing
     `>>> Transport error, retrying in {RETRY_DELAY}s (attempt {attempt}/{MAX_RETRIES})...`
     matching the shape of the two existing lines.
  2. **The `NetworkError` message (`:308-312`)** — today it opens "Claude CLI died with no result event", false for the new route. Split on `not parsed_final`: the existing two-line text for the no-result route unchanged; otherwise first line
     `f"Claude CLI reported a transport failure, exit code {proc.returncode}"`
     and second line `f"result: {result_text[:500]}"` (matching the existing `[:500]` cut at `:323`). Keep it a single `NetworkError(...)` raise — do not add a new exception type; `NetworkError` already covers `"network_halt"`.
  3. **`NetworkError`'s docstring (`:131-133`)** — it claims the CLI "dies before emitting any `result` event". Reword it to cover both routes: a death before any `result` event, and a `result` event whose text names a transport fault — in both cases with retries exhausted.

### Phase 3: Pin the decision table

- [x] **Task 4: Re-label the block, then append five cases** (depends on Task 2)
  Files: `tests/test_agents.py`
  **First, correct the block header (`:540-547`).** It currently reads "Red against the `NotImplementedError` stub — these pin the decision-table contract that a follow-up task fills in; they turn green once the body is implemented." `_classify_result` has had a full body since 18.1.2 (`agents.py:104-120`) and all six cases in the block are green, so the comment states something false and cites the plan layer, which this repo forbids in code and test comments. Appending five never-red cases directly beneath it would widen that false claim. Rewrite it in the present tense, naming what the block groups:
  ```python
  # ---------------------------------------------------------------------------
  # --- _classify_result ---
  # ---------------------------------------------------------------------------
  #
  # The decision table: which terminal action a finished CLI invocation maps to.
  # ---------------------------------------------------------------------------
  ```
  Text only — no assertion, test name, import, or fixture changes, and the `# Task N:` citations elsewhere in the file stay as the deliberate cross-repo evidence Phase 19 left them. The existing `"Row N:"` docstrings on the six cases also stay as they are; the five new cases do **not** adopt that prefix (it indexes a table that lives only in a task spec), and with the header reworded the block reads as one present-tense group.

  **Then append the five cases**, one-line-assert style matching the existing six, which stay untouched and must all still pass:
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
  No case is added for `_is_overloaded`: the extraction is behaviour-preserving and `test_classify_result_overloaded_retry_left` already exercises the predicate through the classifier. Add no import beyond what the file already has (`_classify_result` is imported at `:19`) — the predicates are not tested directly.

## Verify
- `uv run pytest` green: the five new cases plus all six pre-existing `_classify_result` cases unchanged.
- The `_classify_result` block header states present-tense what the block groups: no "red", no "stub", no reference to a follow-up task or any other plan-layer coordinate.
- Manual trace over the incident text (`"API Error: Connection closed mid-response."`, exit `1`, attempt 1 of 3): `_classify_result` returns `"retry"`, not `"error"` — the run survives the first hit.
- Manual trace of the same text through `_run_claude`'s dispatch: with retries remaining the console prints the transport line, not "API overloaded"; with retries spent the raised `NetworkError`'s **first** line names a transport failure with the exit code, not "no result event" — that first line is what `main.py:515` sends to the operator. These two strings are verified by trace, not by a test: asserting them would mean driving the CLI itself.
- `grep -n "overloaded" orchestrator/agents.py` → the substring test now lives only inside `_is_overloaded`; the classifier and the retry print call the predicate.
- Diff touches `orchestrator/agents.py` and `tests/test_agents.py` only; `MAX_RETRIES`/`RETRY_DELAY`, the ratelimit branches, the `is_error` branches, and the markerless-nonzero `"error"` branch are byte-identical.
