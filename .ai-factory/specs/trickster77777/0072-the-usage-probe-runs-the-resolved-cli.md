# The usage probe runs the resolved CLI

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай декомпоуз 29» and «ставим и сохраняем»

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules and § Folder Structure.

What diverges now: [.ai-factory/specs/trickster77777/0067-modules-do-not-yet-follow-the-layer-map.md](0067-modules-do-not-yet-follow-the-layer-map.md).

## What is true now

This is the tree as the tasks above it leave it: `HaltError` comes from `errors`, and `claude_cli.py` holds `_resolve_claude`, `_run_claude` and `kill_active_child`.

`_check_usage_limits(config)` in `orchestrator/usage.py` runs `subprocess.run(["claude", "/usage"], capture_output=True, text=True, timeout=30)` inside a `try` and reads `.stdout`. Its `except Exception` prints `  [usage check: could not parse output, continuing]` and returns. The command is the bare name `claude`, looked up on `PATH` by the process. The agents run the CLI that `_resolve_claude` finds, which falls back to the nvm installs, so on a machine where `claude` is found only that way the probe fails to start and the run continues ungated.

`usage.py` imports `subprocess`. `tests/test_main.py` has `test_check_usage_limits_raises_halt_error_over_threshold`, which patches `usage_module.subprocess.run` with a stand-in whose `stdout` is `"Current session: 99%"`.

## What must be true after

`claude_cli.py` gains `_run_usage_probe() -> str`. It runs `subprocess.run([_resolve_claude(), "/usage"], capture_output=True, text=True, timeout=30)` and returns its stdout.

`_check_usage_limits` calls `_run_usage_probe()` inside its existing `try`; its `except Exception` stays, so a failure to resolve the CLI still reads `[usage check: could not parse output, continuing]`. `usage` imports `_run_usage_probe` from `claude_cli` (the named `usage` → `claude_cli` edge) and no longer imports `subprocess`.

`test_check_usage_limits_raises_halt_error_over_threshold` patches `usage_module._run_usage_probe` with a callable returning `"Current session: 99%"`.

A new test in `tests/test_agents.py`, beside the `claude_cli` tests, patches `claude_cli._resolve_claude` to return a marker path and `claude_cli.subprocess.run` to capture its arguments. It asserts that `_run_usage_probe()` launches `[<marker>, "/usage"]` with `timeout=30` and returns the captured stdout. The test exists because a probe that launches the wrong binary fails nothing at run time.

The one behaviour change of the phase: the usage probe runs the same resolved CLI as the agents. Thresholds, patterns, messages and the fall-through on failure are as before.

## What breaks on contact

- `usage_module.subprocess` no longer exists; the test that patches it, `test_check_usage_limits_raises_halt_error_over_threshold`, patches `usage_module._run_usage_probe`, the name `usage` looks up in its own namespace.
- `docs/features/usage-limits.md` describes the probe as running `claude /usage` and states no lookup rule, so it stays true.
