# Plan: 29.5 — the usage probe runs the resolved CLI

## Context
`_check_usage_limits` in `orchestrator/usage.py` launches `claude /usage` by bare name, so where `claude` is only reachable through `_resolve_claude`'s nvm fallback the probe fails to start and the run continues ungated. This task moves the launch into `claude_cli.py` as `_run_usage_probe()`, which runs the same resolved CLI as the agents (spec: `.ai-factory/specs/trickster77777/0072-the-usage-probe-runs-the-resolved-cli.md`; governing: `.ai-factory/ARCHITECTURE.md` § Dependency Rules — `usage` → `claude_cli` is a named edge, and § Anti-Patterns forbids launching `claude` anywhere but `claude_cli.py`).

Thresholds, patterns, printed messages and the fall-through on failure stay unchanged. `docs/features/usage-limits.md` says only that the probe runs `claude /usage` and gives no lookup rule, so it stays true and is not edited.

## Settings
- Testing: yes (the spec names one adjusted test and one new test)
- Logging: minimal
- Docs: no

## Tasks

### Probe in the CLI adapter

- [x] **Add `_run_usage_probe()` to `claude_cli.py`**
  Files: `orchestrator/claude_cli.py`
  Add a module-level function `_run_usage_probe() -> str`, placed directly after `_run_claude` (the CLI-launching functions stay together). Body: `result = subprocess.run([_resolve_claude(), "/usage"], capture_output=True, text=True, timeout=30)` and `return result.stdout`. Call `_resolve_claude()` directly on each call. Do not read or set the `_CLAUDE_BIN` cache, because the spec pins the call as `_resolve_claude()`. Do not catch exceptions here: a `FileNotFoundError` from `_resolve_claude`, a `subprocess.TimeoutExpired`, or an `OSError` must reach the caller's existing handler. Give it a one-line docstring, e.g. `"""Run the resolved claude CLI's /usage command and return its stdout."""`. `subprocess` is already imported in this module, so no new imports are needed.

- [x] **`_check_usage_limits` calls the probe; `usage` drops `subprocess`** (depends on Add `_run_usage_probe()`)
  Files: `orchestrator/usage.py`
  Remove `import subprocess`. Add `from .claude_cli import _run_usage_probe` next to the existing `from .errors import HaltError` (keep the relative-import style). Inside the existing `try`, replace the two lines `result = subprocess.run(["claude", "/usage"], …)` and `output = result.stdout` with `output = _run_usage_probe()`. The `except Exception:` block, which prints `  [usage check: could not parse output, continuing]` and returns, stays exactly as it is, so a failure to resolve the CLI still takes that path. Leave the rest of the function and the module and function docstrings unchanged.

### Tests

- [x] **Re-point the over-threshold usage test** (depends on `_check_usage_limits` calls the probe)
  Files: `tests/test_main.py`
  In `test_check_usage_limits_raises_halt_error_over_threshold`, remove the `_Result` stand-in class and replace `monkeypatch.setattr(usage_module.subprocess, "run", lambda *a, **kw: _Result())` with `monkeypatch.setattr(usage_module, "_run_usage_probe", lambda: "Current session: 99%")`. `usage` looks the name up in its own namespace, so this patch takes effect. Leave the rest of the test unchanged. Check that nothing else in `tests/` references `usage_module.subprocess` (`grep -rn "usage_module.subprocess\|usage\.subprocess" tests/`) and re-point any hit the same way.

- [x] **New test: the probe launches the resolved CLI** (depends on Add `_run_usage_probe()`)
  Files: `tests/test_agents.py`
  Put it beside the existing `claude_cli` tests, right after `test_sorted_nvm_node_dirs_empty_list_never_raises`, as `test_run_usage_probe_launches_resolved_cli(monkeypatch)`. Patch `claude_cli._resolve_claude` with `lambda: "/marker/bin/claude"`. Patch `claude_cli.subprocess.run` with a fake that records `args` and `kwargs` in a dict and returns an object whose `stdout` is a marker string, e.g. `"Current session: 12%"`. Use `monkeypatch.setattr(claude_cli.subprocess, "run", fake)`, the same style as the existing `claude_cli.subprocess.Popen` patches. Assert:
  - the first positional argument is `["/marker/bin/claude", "/usage"]`;
  - `kwargs["timeout"] == 30`;
  - `claude_cli._run_usage_probe()` returns the marker stdout.
  Give it a short docstring saying the probe must launch the same resolved binary as the agents, because a probe that launches the wrong binary fails silently.

### Verify

- [x] **Run the suite** (depends on all above)
  Files: none
  Run `uv run pytest`. Everything must pass. Also run `grep -n "subprocess" orchestrator/usage.py` and confirm it returns nothing.
