# Plan: 24.1 — No agent is offered work that outlives its turn

## Context
`_run_claude` in `orchestrator/agents.py` launches every agent child with the orchestrator's inherited environment and no deny list, so a backgrounded `Bash`, `Monitor`, `ScheduleWakeup` and `CronCreate` are on offer and an agent that uses one ends its turn with the work orphaned. Every launch gains `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` in its environment and `--disallowedTools Monitor,ScheduleWakeup,CronCreate` on its command line, pinned by one unit test — per the task spec `.ai-factory/specs/trickster77777/0057-no-work-outlives-the-turn.md`, governed by `docs/pipeline.md` § Agent sessions (which already states the intended behaviour; no doc change).

## Settings
- Testing: yes (the task spec requires exactly one unit test in `tests/test_agents.py`)
- Logging: minimal
- Docs: no

## Tasks

### Launch

- [x] **Deny deferred work on every agent launch**
  Files: `orchestrator/agents.py`
  In `_run_claude`:
  - In the base `cmd` list, immediately after the `"--allowedTools", ",".join(allowed_tools),` pair, add two elements: `"--disallowedTools", "Monitor,ScheduleWakeup,CronCreate",`. Keep the literal as one comma-joined string (the option is variadic; the next token is always another flag or the end of `cmd`, and the prompt already sits before both options as the value after `-p`). Do not append it via `cmd.extend` later — it belongs in the base list so every agent, resumed or fresh, carries it.
  - Build the child environment once, before the `for attempt in range(1, MAX_RETRIES + 1):` loop, alongside `cmd`: `env = {**os.environ, "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}` (`os` is already imported). Pass `env=env` to the existing `subprocess.Popen(...)` call inside the loop, next to `cwd=cwd`; every other `Popen` argument stays unchanged.
  Guards: `--allowedTools`, the `allowed_tools` default list, and every agent class's `tools` list stay exactly as they are (narrowing the offered set would take `Edit` from `PlannerReviewer`/`PlanReviewer`, which use it today). Do not touch `usage.py`'s `subprocess.run(["claude", "/usage"], …)` (a one-shot usage read, not an agent turn) or `runtime.py`'s `caffeinate` `Popen` (not the CLI). Do not add a code comment citing the roadmap, a phase, or an `.ai-factory/` path.

### Test

- [x] **Pin the environment and deny list on the launched command** (depends on Deny deferred work on every agent launch)
  Files: `tests/test_agents.py`
  Add a new test in the `--- _run_claude rate-limit halt ---` section, directly after `test_run_claude_ratelimit_halt_has_fixed_first_line`, in its shape; name it by behaviour, e.g. `test_run_claude_launch_denies_work_outliving_the_turn`, with a docstring stating what it pins (no task/phase numbers):
  - Add a stand-in class next to `_FakeRateLimitProc`, shaped like it (`.stdout`, `.wait()`, `.returncode`), e.g. `_FakeOkProc`, whose `stdout` is the single line `['{"session_id": "s1", "result": "ok"}\n']` and whose `returncode` is `0`.
  - Use `monkeypatch.setattr(agents, "_CLAUDE_BIN", "/usr/local/bin/claude")` and the `clean_active_proc` fixture (plus `tmp_path`, `monkeypatch`).
  - Replace `agents.subprocess.Popen` with a callable that records its positional `cmd` (first positional arg) and its `env` keyword into a local dict, then returns the fake proc.
  - Call `agents._run_claude("prompt", cwd=str(tmp_path))`; it must return normally.
  - Assert `recorded["env"]["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"`, and that `"--disallowedTools"` is in the recorded `cmd` and the element immediately after it equals `"Monitor,ScheduleWakeup,CronCreate"` (index-based check, e.g. `cmd[cmd.index("--disallowedTools") + 1]`).
  Run `uv run pytest` and confirm the whole suite passes — the existing rate-limit test's `lambda *a, **kw: fake` keeps working with the new `env` keyword.
