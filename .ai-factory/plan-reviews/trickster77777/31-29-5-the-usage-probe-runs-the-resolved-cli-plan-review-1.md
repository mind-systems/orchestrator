# Plan Review: 29.5 — the usage probe runs the resolved CLI

## Code Review Summary

**Files Reviewed:** 6 (plan; spec `0072`; `orchestrator/usage.py`; `orchestrator/claude_cli.py`; `tests/test_main.py`; `tests/test_agents.py`), plus `.ai-factory/ARCHITECTURE.md`, `docs/features/usage-limits.md`, `orchestrator/main.py` (the caller)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `ARCHITECTURE.md` § Dependency Rules names `usage` → `claude_cli` as an allowed edge. § Anti-Patterns forbids "Launching the `claude` CLI anywhere but `claude_cli.py`", and the bare-name `subprocess.run(["claude", "/usage"], …)` in `usage.py` currently breaks that rule. The plan moves the launch into `claude_cli.py`, which brings the code into line with the rule. Adding the import creates no cycle: `claude_cli` imports only `state` and `errors`, and neither of those imports `usage`.
- **Rules — WARN (missing optional file).** `.ai-factory/RULES.md` does not exist, so this gate has nothing to check.
- **Roadmap — OK.** Contract line 29.5 in `.ai-factory/roadmaps/trickster77777.md` is the first unchecked line, directly after the `[x]` lines for 29.1–29.4. It points to spec `0072`. The plan's four tasks match the spec's "What must be true after" section clause for clause:
  - `_run_usage_probe() -> str` in `claude_cli.py` with the exact `subprocess.run([_resolve_claude(), "/usage"], capture_output=True, text=True, timeout=30)` call;
  - `usage` imports the probe and drops `subprocess`;
  - the over-threshold test is re-pointed to `usage_module._run_usage_probe`;
  - a new `claude_cli` test asserts the resolved path, `/usage`, `timeout=30`, and that stdout is returned.

### Verification against the code

- `usage.py` matches what the plan describes: `import subprocess`, `from .errors import HaltError`, and the two lines `result = subprocess.run([...])` / `output = result.stdout` inside a `try` whose `except Exception:` prints `  [usage check: could not parse output, continuing]`. The plan's replacement keeps that handler, so a `FileNotFoundError` from `_resolve_claude` still falls through as the spec requires.
- `claude_cli.py` already imports `subprocess`, and `_run_claude` is the CLI-launching function the new probe will sit next to. The plan has the probe call `_resolve_claude()` directly rather than reuse the `_CLAUDE_BIN` cache, which matches the spec. It also keeps the new test independent of cache state left behind by other tests (`test_agents.py` patches `_CLAUDE_BIN` via monkeypatch in its `_run_claude` tests).
- `tests/test_main.py` imports `usage as usage_module`, and the only `usage_module.subprocess` reference is in `test_check_usage_limits_raises_halt_error_over_threshold`, which is the test the plan re-points. Patching `usage_module._run_usage_probe` works because `usage` binds the name in its own namespace through `from .claude_cli import _run_usage_probe`. The plan's grep step for other hits is a cheap safety net.
- `tests/test_agents.py` has `test_sorted_nvm_node_dirs_empty_list_never_raises` at the end of the `claude_cli` resolver block, so the planned placement exists. The planned patch, `monkeypatch.setattr(claude_cli.subprocess, "run", fake)`, uses the same style as the existing `claude_cli.subprocess.Popen` patches. The module-level `subprocess` patch is undone at teardown, so it does not leak into other tests.
- The only caller is `main.py`, at `_check_usage_limits(config)` inside the task loop. Its signature and behaviour do not change, so the caller needs no edit.
- The plan explains why `docs/features/usage-limits.md` stays unedited. The page says the orchestrator "runs `claude /usage`" and gives no rule for how the binary is found, so it remains true. The spec's "What breaks on contact" section says the same.

### Critical Issues

None.

### Positive Notes

- The plan decides each edge case the implementer would otherwise have to guess: no exception handling in the probe, no use of the `_CLAUDE_BIN` cache, and the exact import placement and style.
- The new test checks the one silent-failure surface, a probe that launches the wrong binary. A wrong binary crashes nothing; it only skips the usage gate. The test exists because of that risk, not to raise coverage.
- The Verify step adds `grep -n "subprocess" orchestrator/usage.py` to confirm the import is gone, which `pytest` alone would not catch.

## Deferred observations

- Affects: unknown (a test-hygiene cleanup outside spec `0072`) — In `tests/test_main.py`, the section comment above `test_check_usage_limits_raises_halt_error_over_threshold` says "both currently raise PipelineStopError, both should raise HaltError once task 05 lands". The test's docstring says "(red now — currently raises PipelineStopError)". Both are stale, because the code already raises `HaltError`. The comment also cites a plan-layer task number, which the global documentation style forbids in code comments. These lines predate this task, and spec `0072` leaves the rest of the test unchanged, so this plan does not fix them. A separate cleanup should rewrite the comment and docstring in the present tense.

PLAN_REVIEW_PASS
