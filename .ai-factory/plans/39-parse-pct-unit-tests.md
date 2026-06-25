# Test Plan: `_parse_pct` unit tests

## Context
`_parse_pct(text, pattern)` (`orchestrator/main.py:30-33`) runs `re.search(pattern, text)` and returns the first captured group as a `float`, or `None` when there is no match. These tests pin that behavior using the two real production patterns from `main.py:45-46`.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/test_main.py`

## Target Spec File
`tests/test_main.py`

## Tasks

### Phase 1: `_parse_pct` — match and capture behavior

- [x] **Task 1: Successful matches return the captured percentage as a float**
  Files: `tests/test_main.py`
  Import: `from orchestrator.main import _parse_pct`
  Use the production patterns verbatim:
  - session: `r"Current session:\s+(\d+(?:\.\d+)?)%"`
  - weekly: `r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%"`
  Test cases:
  - `should return 85.0 when session pattern matches "Current session: 85%"`
  - `should return 42.5 when weekly pattern matches "Current week (all models): 42.5%"`
  - `should return 12.3 when session pattern matches a decimal "Current session: 12.3%"`
  - `should return a float instance (not a string) on a successful match` (assert via `isinstance(result, float)`)

- [x] **Task 2: Non-matching input returns None**
  Files: `tests/test_main.py`
  Test cases:
  - `should return None when session pattern finds no match in unrelated text`
  - `should return None when text contains unrelated digits "used 5 tokens" and does not match the session pattern`

### Phase 2: `_parse_pct` — multi-line / first-match semantics

- [x] **Task 3: re.search scans the whole string, returning the first match anywhere**
  Files: `tests/test_main.py`
  Test cases:
  - `should return the first matching percentage when given a multi-line output string` (build a multi-line string where the first line has no match and a later line contains e.g. "Current session: 70%"; assert 70.0 — proves `re.search` is not line-anchored)
