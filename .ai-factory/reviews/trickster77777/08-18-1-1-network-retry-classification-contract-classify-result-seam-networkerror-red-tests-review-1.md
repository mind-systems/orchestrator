## Code Review — 18.1.1 Network/retry classification contract

**Files reviewed (in full):** `orchestrator/agents.py`, `tests/test_agents.py`
**Verification run:** `uv run pytest tests/test_agents.py -q` → 6 failed, 39 passed; import + subclass check confirmed.
**Risk level:** 🟢 Low — contract-only commit (type + stub + red tests), no runtime path rewired.

### Scope conformance
The diff touches exactly `agents.py` (type + seam) and `tests/test_agents.py` (red tests), as the spec's "What NOT to do" mandates. `_run_claude`'s inline classification at `agents.py:229-258` and the empty-stdout guard are left untouched. Nothing wired.

### Correctness

- **`NetworkError`** subclasses `HaltError` (verified `issubclass(NetworkError, HaltError) is True`), placed directly beside `RateLimitError`. Base class is correct — not `Exception`, not `RateLimitError` — so a later `except HaltError` catches it as a clean halt. ✓
- **`_classify_result`** has the exact spec signature (six params, `-> str`), a stub body of `raise NotImplementedError`, and a docstring documenting the five return literals plus the `no_result = not parsed_final` meaning. Pure, no I/O. ✓
- **Placement** — the function sits below `_write_session` and above `HaltError`. The stub references neither `HaltError` nor `NetworkError`, so being defined before them raises no NameError; module imports cleanly. Even after 18.1.2 the classifier only *returns* the `"network_halt"` string (the raise lives in `_run_claude`), so no forward-reference hazard is introduced by this ordering. ✓
- **Red tests** — six tests, one per contract row, asserting the return value directly (not wrapping in `pytest.raises`), so they fail red now against the stub and turn green when 18.1.2 fills the body. All six failures are `NotImplementedError` from the stub — no accidental collection/import error masking a different failure.

### Decision-table fidelity (each test input traced through spec 33's precedence table)
Confirmed every pinned input resolves to its asserted literal under the spec's top-to-bottom precedence, so these are correct green targets for 18.1.2, not merely red today:

- Row 2 `({}, "", 1, False, 1, 3)` → `no_result` ∧ `rc≠0` ∧ `attempt<max` ⇒ `"retry"` ✓
- Row 3 `({}, "", 1, False, 3, 3)` → `no_result` ∧ `rc≠0`, exhausted ⇒ `"network_halt"` ✓
- Row 1 `({"result":"overloaded"}, "overloaded", 0, False, 1, 3)` → overloaded ∧ retry left ⇒ `"retry"` (non-empty `parsed_final` ⇒ `no_result` False; no row-2 collision) ✓
- Row 5 `({"result":"boom"}, "boom", 1, False, 3, 3)` → `rc≠0`, no rate-limit token, retries exhausted (rows 1/2 disabled) ⇒ `"error"` ✓
- Row 4 `({"result":"You hit your limit"}, ..., 1, False, 3, 3)` → `rc≠0` ∧ "hit your limit" ⇒ `"ratelimit"` ✓
- Row 8 `({"result":"done","is_error":False}, "done", 0, False, 1, 3)` → `"ok"` ✓

### Notes
- Rows 6/7 (`is_error` with `rc==0`) are unpinned, matching the spec's own test list — a deliberate scope boundary, not a coverage gap for this task.
- No test for `NetworkError` subclassing, consistent with test-philosophy: a wrong base class fails loudly at 18.1.2 wiring time.
- Every pre-existing test stays green (39 passed); the intentionally-failing six are the contract's red target, not a regression.

No correctness, security, or runtime concerns.

REVIEW_PASS
