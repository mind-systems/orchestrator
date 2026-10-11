## Code Review Summary

**Files Reviewed:** 4 code files (`orchestrator/claude_cli.py`, `orchestrator/usage.py`, `tests/test_agents.py`, `tests/test_main.py`), plus the plan, the plan review and the sidecar
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `ARCHITECTURE.md` § Dependency Rules names `usage` → `claude_cli` as an allowed edge, and this diff uses only that edge. `claude_cli` imports only `state` and `errors`, so there is no import cycle. § Anti-Patterns forbids "Launching the `claude` CLI anywhere but `claude_cli.py`". Before this diff `usage.py` launched `claude` itself; after it, no module outside `claude_cli.py` does. The `subprocess.run` calls left in `agents.py`, `main.py` and `resume.py` run the TestRunner's command and git, not `claude`.
- **Rules — WARN (missing optional file).** `.ai-factory/RULES.md` does not exist.
- **Roadmap — OK.** Contract line 29.5 in `.ai-factory/roadmaps/trickster77777.md` matches spec `0072`, and the diff meets each clause of the spec's "What must be true after" section:
  - `_run_usage_probe() -> str` runs exactly `subprocess.run([_resolve_claude(), "/usage"], capture_output=True, text=True, timeout=30)` and returns `.stdout`;
  - `_check_usage_limits` calls the probe inside the unchanged `try`, and its `except Exception` is kept;
  - `usage.py` imports `_run_usage_probe` from `.claude_cli` and no longer imports `subprocess`;
  - the over-threshold test patches `usage_module._run_usage_probe`;
  - the new `claude_cli` test asserts the resolved path, `/usage`, `timeout=30`, and that stdout is returned.

### Verification

- `_resolve_claude()` is called inside the `try` in `_check_usage_limits`, through the probe. A `FileNotFoundError` when no CLI is found therefore still prints `  [usage check: could not parse output, continuing]` and returns, as the spec requires. `TimeoutExpired` and `OSError` take the same path.
- The probe does not touch the `_CLAUDE_BIN` cache, which matches the spec. The new test therefore does not depend on cache state left by the `_run_claude` tests.
- `usage_module._run_usage_probe` is bound in `usage`'s own namespace by the `from` import, so the re-pointed patch takes effect. No other test references `usage_module.subprocess`.
- The only caller is `main.py`'s `_check_usage_limits(config)`, and its signature is unchanged.
- `uv run pytest`: 227 passed.

### Critical Issues

None.

### Positive Notes

- The change is minimal and exactly scoped. The probe has no error handling of its own, so the caller's existing fall-through stays the single place where a probe failure is handled.
- The new test covers the one silent-failure surface. If the probe launched the wrong binary, nothing would crash and the run would simply go ungated.
- The test patches `claude_cli.subprocess.run` the same way the existing `claude_cli.subprocess.Popen` tests patch `Popen`.

## Deferred observations

- Affects: unknown (test-hygiene cleanup outside spec `0072`) — `tests/test_main.py` has two stale remarks about `test_check_usage_limits_raises_halt_error_over_threshold`, which the code no longer matches because `_check_usage_limits` already raises `HaltError`:
  - the section comment above the test says "both currently raise PipelineStopError, both should raise HaltError once task 05 lands". It also cites a plan-layer task number, which the documentation style forbids in code comments;
  - the test's docstring says "(red now — currently raises PipelineStopError)".

  Both predate this task. The plan tells the implementer to leave the rest of the test unchanged, so fixing them here would contradict the plan. A separate cleanup should rewrite them in the present tense.

REVIEW_PASS
