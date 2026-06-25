# Test Plan: `_has_signal` unit tests

## Context
`_has_signal(text, signal)` (`orchestrator/agents.py:42-44`) decides pipeline pass/fail by checking whether `signal` appears as an exact, whitespace-stripped line within the **last 5 lines** of `text`. These tests pin its window boundary and exact-match semantics.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/test_agents.py -v`

## Target Spec File
`tests/test_agents.py`

## Tasks

### Phase 1: `_has_signal` — exact-match and window behavior

- [x] **Task 1: `_has_signal` — match within the last-5-line window**
  Files: `tests/test_agents.py`
  Import under test: `from orchestrator.agents import _has_signal`
  Test cases:
  - `should return True when signal is the exact last line` — single-line or multi-line text whose final line equals the signal (e.g. `"...\nREVIEW_PASS"`).
  - `should return True when signal is on line 3 of a 5-line text` — non-last line but still inside the last-5 window (`splitlines()[-5:]` covers all 5 lines).
  - `should return True when signal is on line 6 of a 10-line text` — first line inside the window (index 5, the start of `[-5:]`).
  - `should return True when signal is PLAN_REVIEW_PASS on the last line` — verifies the function is signal-agnostic, not hardcoded to `REVIEW_PASS`.

- [x] **Task 2: `_has_signal` — window exclusion and exact-match rejection**
  Files: `tests/test_agents.py`
  Test cases:
  - `should return False when signal is on line 5 of a 10-line text` — line just outside the last-5 window (index 4, excluded by `[-5:]`).
  - `should return False when signal appears only as a substring of a longer line` — e.g. `"no REVIEW_PASS here"`; `.strip() == signal` requires the whole stripped line to equal the signal.
  - `should return True when the signal line has surrounding whitespace` — e.g. `"  REVIEW_PASS  "`; `.strip()` removes leading/trailing whitespace before comparison.
  - `should return False when text is empty` — `"".splitlines()` yields `[]`, so `any(...)` over no lines is `False`.
