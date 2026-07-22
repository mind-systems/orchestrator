# Plan: 18.1.1 — Network/retry classification contract: `_classify_result` seam + `NetworkError` + red tests

## Context
Lay the pure, testable seam that the retry/halt decision in `_run_claude` will later move onto: add a `NetworkError` halt type, a stubbed `_classify_result` pure function, and red unit tests pinning its 8-row decision table. This is a contract-only commit (compiles, tests red) — the body and the rewiring are task 18.1.2.

## Settings
- Testing: yes (red unit tests are the deliverable)
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Type + seam

- [x] **Task 1: Add the `NetworkError` halt type**
  Files: `orchestrator/agents.py`
  Directly beside `RateLimitError` (`agents.py:73`), add `class NetworkError(HaltError):` with a one-line docstring stating it is raised when the Claude CLI dies before emitting any `result` event (transient network/infra death) and retries are exhausted. It must subclass `HaltError` (not `Exception`, not `RateLimitError`) so a later `except HaltError` in `main.py` catches it as a clean halt. No wiring — just the type.

- [x] **Task 2: Add the stubbed `_classify_result` pure seam** (depends on Task 1)
  Files: `orchestrator/agents.py`
  Add a module-level pure function with the exact signature from the spec:
  ```python
  def _classify_result(parsed_final: dict, result_text: str, returncode: int,
                       is_error: bool, attempt: int, max_retries: int) -> str:
  ```
  Returns one of the literals `"retry" | "ratelimit" | "network_halt" | "error" | "ok"`. Body is a stub: `raise NotImplementedError`. Include a docstring documenting the return-value contract and the `no_result = not parsed_final` meaning, but do NOT implement the decision table — that is 18.1.2. Place it near the other module-level helpers (e.g. below `_write_session` / above `HaltError` or adjacent to the other pure helpers), so it is importable as `orchestrator.agents._classify_result`. Do NOT rewire `_run_claude` — its inline logic at `agents.py:229-258` stays untouched, and the empty-stdout guard stays inline.

### Phase 2: Red tests

- [x] **Task 3: Add red unit tests for `_classify_result`** (depends on Task 2)
  Files: `tests/test_agents.py`
  Add a new section (follow the existing `# ---` banner-comment style) importing `_classify_result` from `orchestrator.agents`. Add one test per contract row, calling `_classify_result` directly (no subprocess), asserting the expected literal. These run **red** against the `NotImplementedError` stub — wrap each call in `pytest.raises(NotImplementedError)` is NOT wanted; instead assert the target return value directly so the test fails against the stub and turns green in 18.1.2. Cases (mirroring the spec's decision table, precedence top-to-bottom):
  - Row 2 — network death, retry left: `_classify_result({}, "", 1, False, 1, 3) == "retry"`.
  - Row 3 — network death, exhausted: `_classify_result({}, "", 1, False, 3, 3) == "network_halt"`.
  - Row 1 — overloaded, retry left: `_classify_result({"result": "overloaded"}, "overloaded", 0, False, 1, 3) == "retry"`.
  - Row 5 — real CLI error: `_classify_result({"result": "boom"}, "boom", 1, False, 3, 3) == "error"`.
  - Row 4 — rate limit (returncode path): `_classify_result({"result": "You hit your limit"}, "You hit your limit", 1, False, 3, 3) == "ratelimit"`.
  - Row 8 — clean success: `_classify_result({"result": "done", "is_error": False}, "done", 0, False, 1, 3) == "ok"`.
  Each test gets a docstring naming the contract row it pins. Do not add tests for the `NetworkError` subclassing (loud surface — a wrong base class fails at wiring time in 18.1.2).

### Verify

- `uv run pytest` compiles and runs; the six `_classify_result` tests are **red** (stub raises `NotImplementedError`); every pre-existing test stays **green** (nothing rewired).
- `NetworkError` is importable and `issubclass(NetworkError, HaltError)` holds.
