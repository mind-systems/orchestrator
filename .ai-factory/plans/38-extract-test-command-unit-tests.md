# Test Plan: `_extract_test_command` unit tests

## Context
`TestRunner._extract_test_command` (`orchestrator/agents.py:435`) parses the `## Test Command` section of a plan file and returns the command string (or `None`). These tests lock in its section-scanning, backtick-stripping, and boundary behavior.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/test_agents.py -v`

## Target Spec File
`tests/test_agents.py`

## Notes for the Implementer
- Import: `from orchestrator.agents import TestRunner`.
- Call as `TestRunner._extract_test_command(plan_path)` — it is a `@staticmethod`.
- Use the `tmp_path` pytest fixture to write a plan file, e.g. `p = tmp_path / "plan.md"; p.write_text(...)`, then pass `p`.
- Follow the existing style in this file: plain `def test_...()` functions with a one-line docstring, plain `assert`. Group with comment banners as already done.
- Source logic being exercised (`agents.py:435-452`): scan lines until `line.strip() == "## Test Command"`, then for each following line — break if `stripped.startswith("#")`; if `stripped.startswith("`") and stripped.endswith("`")` return `stripped.strip("`")`; else if `stripped` is non-empty return it as-is; blank lines are skipped. Returns `None` if no command found.

## Tasks

### Phase 1: TestRunner._extract_test_command — extraction & stripping

- [x] **Task 1: backtick-wrapped command**
  Files: `tests/test_agents.py`
  Test cases:
  - `should return the command without backticks when the command line is wrapped in single backticks` — body `## Test Command\n\`uv run pytest tests/ -v\`` → `"uv run pytest tests/ -v"` (exercises the `startswith("\`") and endswith("\`")` → `strip("\`")` branch, `agents.py:448`)

- [x] **Task 2: bare command without backticks**
  Files: `tests/test_agents.py`
  Test cases:
  - `should return the command string as-is when the command line has no backticks` — body `## Test Command\nuv run pytest tests/ -v` → `"uv run pytest tests/ -v"` (exercises the `if stripped:` fallthrough, `agents.py:450`)

- [x] **Task 3: command after intervening blank lines**
  Files: `tests/test_agents.py`
  Test cases:
  - `should return the first non-empty non-heading line when blank lines follow the heading` — body `## Test Command\n\n\nuv run pytest -v` → `"uv run pytest -v"` (blank `stripped` is falsy, loop continues until first non-empty line; confirms case 5)

### Phase 2: TestRunner._extract_test_command — None paths

- [x] **Task 4: heading absent**
  Files: `tests/test_agents.py`
  Test cases:
  - `should return None when the plan has no Test Command heading` — body e.g. `# Some Plan\n## Other Section\nrun this` with no `## Test Command` line → `None` (`in_section` never set, falls through to `return None`, `agents.py:452`)

- [x] **Task 5: empty section before next heading**
  Files: `tests/test_agents.py`
  Test cases:
  - `should return None when the Test Command section is blank up to the next heading` — body `## Test Command\n\n## Next Section\nuv run pytest` → `None` (blank lines skipped, then `## Next Section` triggers the `startswith("#")` break before any command, `agents.py:446`); the command under the next heading must not be returned
