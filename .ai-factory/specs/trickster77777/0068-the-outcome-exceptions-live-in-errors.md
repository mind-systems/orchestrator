# The outcome exceptions live in errors.py

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай декомпоуз 29» and «ставим и сохраняем»

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules and § Folder Structure.

What diverges now: [.ai-factory/specs/trickster77777/0067-modules-do-not-yet-follow-the-layer-map.md](0067-modules-do-not-yet-follow-the-layer-map.md).

## What is true now

`orchestrator/agents.py` defines the outcome exceptions, each with its docstring:

- `HaltError(Exception)`, the operational halt, and its subclasses `RateLimitError`, `NetworkError` and `MissingArtifactError`;
- `PipelineStopError(Exception)`;
- `EscalationError(Exception)`, a deliberate sibling of `PipelineStopError` and not a `HaltError` subclass.

`main.py` imports `EscalationError`, `HaltError` and `PipelineStopError` from `agents`. `usage.py` imports `HaltError` from `agents`, the only thing it takes from it. `agents.py` raises them in `_run_claude` and in the roles. `tests/test_agents.py` imports `EscalationError`, `HaltError`, `MissingArtifactError` and `RateLimitError` from `agents`; `tests/test_main.py` imports `EscalationError`, `HaltError`, `PipelineStopError` and `RateLimitError` from `agents`, and `test_check_usage_limits_raises_halt_error_over_threshold` reads `HaltError` as `getattr(agents_module, "HaltError", None)`.

## What must be true after

A new `orchestrator/errors.py` defines `HaltError`, `RateLimitError`, `NetworkError`, `MissingArtifactError`, `PipelineStopError` and `EscalationError`, bases and bodies unchanged, docstrings included. It imports nothing from the package.

`agents`, `main` and `usage` import the names they use from `errors`; `agents` re-exports nothing. The tests import the exceptions from `errors`, and `test_check_usage_limits_raises_halt_error_over_threshold` reads `HaltError` from `errors`. `usage` no longer imports `agents`.

The change is behaviour-neutral: no message, outcome or notification changes.

## What breaks on contact

- No test patches an exception name; the tests import and raise them. The import lines in `tests/test_agents.py` and `tests/test_main.py` change.
- `test_check_usage_limits_raises_halt_error_over_threshold` reads `agents_module.HaltError` by `getattr` with a default; with no re-export it gets `None` and fails its assertion. It reads `errors` instead.
- A re-export left in `agents` would keep every old import working and hide a missed one; `agents` has none.
