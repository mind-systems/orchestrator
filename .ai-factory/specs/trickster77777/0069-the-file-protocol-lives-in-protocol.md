# The file protocol lives in protocol.py

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай декомпоуз 29» and «ставим и сохраняем»

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules and § Folder Structure.

What diverges now: [.ai-factory/specs/trickster77777/0067-modules-do-not-yet-follow-the-layer-map.md](0067-modules-do-not-yet-follow-the-layer-map.md).

## What is true now

This is the tree as the task "the outcome exceptions live in `errors.py`" leaves it.

`orchestrator/agents.py` holds the file protocol beside the roles and the CLI runner:

- `_read_sessions(plan_path)` returns the sidecar next to the plan as a dict, empty when it is absent or unreadable;
- `_write_session(plan_path, key, value)` sets one key atomically through a temporary file and `os.replace`;
- `_has_signal(text, signal)` is true when the signal stands as an exact line among the text's last five lines;
- `_has_escalation(text)` is `_has_signal(text, "ESCALATION")`;
- `_escalation_excerpt(text)` returns the first non-empty, non-heading line under a `## Escalation` section.

The roles in `agents.py` call them. `main.py` imports `_read_sessions` and `_write_session` from `agents`; `resume.py` imports `_read_sessions` from `agents`. `tests/test_agents.py` imports all of them from `agents`.

## What must be true after

A new `orchestrator/protocol.py` defines `_read_sessions`, `_write_session`, `_has_signal`, `_has_escalation` and `_escalation_excerpt`, bodies and docstrings unchanged. It imports nothing from the package.

`agents`, `main`, `resume` and the tests import them from `protocol`; `agents` no longer defines them and re-exports nothing.

The change is behaviour-neutral: the sidecar, its keys and the recognition rule are as before.

## What breaks on contact

- No test patches these names. The tests that exercise them import them (`tests/test_agents.py`) and use real files under `tmp_path`.
- Import lines change in `tests/test_agents.py`, `main.py`, `resume.py` and the roles in `agents.py`.
- The role tests that patch `agents._run_claude` stay valid: the roles look `_run_claude` up in `agents`, and nothing here moves it.
