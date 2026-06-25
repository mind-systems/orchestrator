# Plan Review: `_extract_test_command` unit tests

**Plan:** `38-extract-test-command-unit-tests.md`
**Files Reviewed:** plan + `orchestrator/agents.py` (435-452), `tests/test_agents.py`, `tests/conftest.py`, `pyproject.toml`, `ROADMAP_TESTS.md`
**Risk Level:** 🟢 Low

## Context Gates
- **Architecture** (`ARCHITECTURE.md` present): OK — pure test addition, no boundary/dependency impact.
- **Rules** (`RULES.md` absent): WARN — no project rules file; nothing to enforce.
- **Roadmap** (`ROADMAP_TESTS.md`): OK — plan maps 1:1 to the `` `_extract_test_command` unit tests `` milestone (line 13). All five roadmap cases are represented in the plan's 5 tasks.

## Verification Against Source

I traced every task against `agents.py:435-452`. The plan's claims are all correct:

| Task | Input | Expected | Source branch | Verdict |
|------|-------|----------|---------------|---------|
| 1 | `` `uv run pytest tests/ -v` `` | `uv run pytest tests/ -v` | `:448` backtick strip | ✅ correct |
| 2 | bare command | returned as-is | `:450` `if stripped:` | ✅ correct |
| 3 | blank lines then command | first non-empty line | blank `stripped` falsy → loop continues | ✅ correct |
| 4 | no `## Test Command` heading | `None` | `in_section` never set → `:452` | ✅ correct |
| 5 | blank then `## Next Section` | `None` | `:446` `startswith("#")` break | ✅ correct |

Task 4 detail confirmed: `## Other Section` does not equal `## Test Command`, so `in_section` stays `False` and the body line `run this` is never returned. Task 5 detail confirmed: the break on `## Next Section` fires before the command under it is reached.

## Notes (non-blocking)

- **Line-number drift (minor):** The plan's Context cites `agents.py:435` for the method; line 435 is the `@staticmethod` decorator and 436 is the `def`. The roadmap entry cites `:434`. Both are off-by-one/two but point at the right method — harmless. No action required.
- **Module docstring:** `tests/test_agents.py` opens with `"""Unit tests for _has_signal."""`. After adding `_extract_test_command` tests the docstring becomes inaccurate. Consider broadening it (e.g. "Unit tests for agents helpers"), though the plan's "follow existing style" instruction is otherwise sound.
- **Import addition:** The file currently imports only `_has_signal`. The implementer must add `TestRunner` to the imports (the plan already specifies `from orchestrator.agents import TestRunner`). No conflict.
- **Coverage is appropriate:** The plan covers backtick strip, bare fallthrough, blank-skipping, missing-heading None, and next-heading-break None — the full behavior surface of a 17-line function. No meaningful path is left untested; no over-engineering.

## Positive Notes
- Each test case names the exact source branch it exercises, making intent auditable.
- Correctly identifies that `_extract_test_command` is a `@staticmethod` and can be called on the class without instantiation — avoiding a needless `TestRunner()` construction.
- Uses `tmp_path` for filesystem fixtures rather than mocking `read_text`, which keeps the tests honest about real file parsing.
- Negative paths (Tasks 4–5) are included, not just happy paths.

The plan is accurate, complete, and implementable as written.

PLAN_REVIEW_PASS
