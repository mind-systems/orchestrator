# No agent is offered work that outlives its turn

**Date:** 2026-09-28
**Source:** a plan reviewer on `tradeoxy_core` (session `dcd51185-8b0e-470a-882a-d4b707e5f706`) that backgrounded its baseline `tsc`/Jest run, ended its turn with "I'll write the review once it finishes", and never wrote it

Governing spec: [pipeline.md § Agent sessions](../../../docs/pipeline.md) — an agent's turn is the whole of its life, so no agent is offered work that outlives it.

## What is true now

`_run_claude` in `orchestrator/agents.py` launches every agent — `PlannerReviewer`, `PlanReviewer`, `Implementer` — as `claude -p … --output-format stream-json --verbose --dangerously-skip-permissions --allowedTools <agent.tools>`, through `subprocess.Popen(cmd, cwd=cwd, …)` with no `env` argument, so the child inherits the orchestrator's environment unchanged.

`-p` is one turn: when the agent ends its turn the CLI emits its `result` event and exits, and `_run_claude` returns. Nothing re-invokes the session afterwards.

`--allowedTools` approves the tools it names; it does not restrict the set the agent is offered. Under `--dangerously-skip-permissions` every built-in tool is available, including the three that let an agent defer work past its turn:

- `Bash` with `run_in_background: true` — returns at once with an output-file path; the command keeps running after the turn ends.
- `Monitor` — reached through `ToolSearch`; streams a background command's events back as later notifications.
- `ScheduleWakeup` — schedules a later turn.

In the source session the reviewer called `Bash` with `run_in_background: true` for `npx tsc --noEmit` and `npx jest src/indicators`, loaded `Monitor` through `ToolSearch`, launched a second backgrounded `Bash` that polled for the Jest exit line, and ended its turn. The process exited, the backgrounded commands were orphaned, and the review file was never written. Across 553 headless pipeline sessions in the preceding 14 days: 6 backgrounded `Bash` calls and 1 `ScheduleWakeup`.

Measured against `claude` 2.1.281 in `-p` mode:

- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` in the child's environment removes `run_in_background` from the `Bash` schema — a call that passes it fails with `InputValidationError: … An unexpected parameter 'run_in_background' was provided`, and the agent carries on in the foreground.
- `--disallowedTools Monitor` removes `Monitor` from the session's tool list; `--disallowedTools` applies under `--dangerously-skip-permissions`.

## What must be true after

Every child `_run_claude` launches runs with:

- an environment that is the orchestrator's own plus `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` — `env={**os.environ, "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}` on the `Popen` call;
- `--disallowedTools Monitor,ScheduleWakeup,CronCreate` on the command line — two elements of `cmd`, `"--disallowedTools"` and the literal `"Monitor,ScheduleWakeup,CronCreate"`, in the base list right after the `"--allowedTools", ",".join(allowed_tools)` pair. The option is variadic (`--disallowedTools <tools...>`); the next token is always another flag or the end of `cmd`, which ends the list, and the prompt is already placed before both options as the value after `-p`.

Both hold for every attempt of `_run_claude`'s retry loop and for every agent class, resumed session or fresh — they are properties of the launch, not of any one agent. `cmd` and the environment are both built before the retry loop, so every attempt reuses them.

A unit test in `tests/test_agents.py`, beside `test_run_claude_ratelimit_halt_has_fixed_first_line` and in its shape: `monkeypatch.setattr(agents, "_CLAUDE_BIN", "/usr/local/bin/claude")`, the `clean_active_proc` fixture, and `agents.subprocess.Popen` replaced by a lambda that records its positional `cmd` and its `env` keyword and returns a stand-in shaped like `_FakeRateLimitProc` (`.stdout`, `.wait()`, `.returncode`) whose `stdout` is the single line `{"session_id": "s1", "result": "ok"}` and whose `returncode` is `0`. `_run_claude("prompt", cwd=str(tmp_path))` returns normally, and the test asserts the recorded `env["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"` and that the recorded `cmd` holds `"--disallowedTools"` immediately followed by `"Monitor,ScheduleWakeup,CronCreate"`. A regression here fails silently — a run works until the one session that backgrounds — which is the kind of surface this project tests.

## What breaks on contact

- `--allowedTools` and each agent's `tools` list stay exactly as they are. Restricting the offered set to the declared list (`--tools`) would take `Edit` away from `PlannerReviewer` and `PlanReviewer`, which declare only `Read, Write, Glob, Grep, Bash` yet use `Edit` today — that is a different change with its own blast radius.
- An agent that would have backgrounded a slow command now runs it in the foreground and waits for it. A long `tsc`/Jest run lengthens that agent's turn; nothing in the orchestrator bounds a turn's wall-clock, so nothing trips.
- The affected set is every site that launches the `claude` CLI. Sweep: `rg -n '"claude"|_CLAUDE_BIN|Popen\(' orchestrator/`. Run now, it reaches three launches: `_run_claude`'s `subprocess.Popen` — this task's target and the only agent launch; `_check_usage_limits`' `subprocess.run(["claude", "/usage"], …)` in `orchestrator/usage.py` — a one-shot read of usage output, not an agent turn, left unchanged; and `_with_caffeinate`'s `Popen(["caffeinate", "-ims"])` in `orchestrator/runtime.py` — not the CLI at all. The remaining matches are `_resolve_claude`'s binary lookup and `_CLAUDE_BIN`'s own declaration and reads.
- No existing test asserts on the launched command or environment; `test_run_claude_ratelimit_halt_has_fixed_first_line`'s `Popen` lambda takes `*a, **kw` and keeps working when `env` is added.
