## Plan Review Summary

**Plan:** 24.1 — No agent is offered work that outlives its turn
**Files Reviewed:** `orchestrator/agents.py` (`_run_claude`, `_classify_result`), `tests/test_agents.py` (the `_run_claude rate-limit halt` section, the `clean_active_proc` fixture), `orchestrator/usage.py`, `orchestrator/runtime.py`, `docs/pipeline.md` § Agent sessions, task spec `.ai-factory/specs/trickster77777/0057-no-work-outlives-the-turn.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** — OK. The change stays inside `_run_claude` in `agents.py`, which is the only place that launches an agent. It adds no new module and crosses no boundary.
- **Rules** — WARN (non-blocking): `.ai-factory/RULES.md` does not exist, so there are no explicit conventions to check against. The plan follows the global comment rule: it says no code comment may cite the roadmap, a phase, or an `.ai-factory/` path.
- **Roadmap** — OK. The plan title matches contract line **24.1** in `.ai-factory/roadmaps/trickster77777.md`. That line's `Spec:` tag resolves to `specs/trickster77777/0057-no-work-outlives-the-turn.md`, and the plan names the same file.
- **Governing spec** — OK. `docs/pipeline.md` § Agent sessions already describes the intended behaviour in the present tense ("no tool that waits, watches, or schedules on the agent's behalf is available"). The plan correctly says no doc change is needed.

### Verification against ground truth
- `_run_claude` builds `cmd` as a base list that ends with the `"--allowedTools", ",".join(allowed_tools),` pair. It then calls `cmd.extend` for `--model`, `--effort`, `--resume` and `--system-prompt`. The single `subprocess.Popen(cmd, cwd=cwd, …)` call sits inside `for attempt in range(1, MAX_RETRIES + 1):` and has no `env` argument. The plan's insertion points match the code exactly.
- `os` is already imported in `agents.py`, so building `env` needs no new import.
- The option is variadic, and the plan puts it in the right place. After `--disallowedTools <list>` the next token is always another flag (`--model`, `--effort`, `--resume`, `--system-prompt`) or the end of `cmd`. The prompt is the value after `-p`, earlier in the list. So the deny list cannot swallow a positional argument.
- The sweep with `rg -n '"claude"|_CLAUDE_BIN|Popen\('` finds the three sites the spec names. The only agent launch is `_run_claude`. `usage.py`'s `subprocess.run(["claude", "/usage"], …)` and `runtime.py`'s `Popen(["caffeinate", "-ims"])` are the other two, and the plan's guards leave both unchanged.
- The test's success path works. With a stand-in stdout of `{"session_id": "s1", "result": "ok"}`, `returncode` 0 and no `is_error`, `_classify_result` falls through to `"ok"`. `lines` is non-empty and `sid` resolves to `"s1"`, so `_run_claude` returns normally without calling `time.sleep`.
- The existing `test_run_claude_ratelimit_halt_has_fixed_first_line` replaces `Popen` with `lambda *a, **kw: fake`, which still accepts the new `env` keyword.
- The guard on `--allowedTools` and each agent's `tools` list is taken from the spec's "What breaks on contact" section.

### Critical Issues
None.

### Positive Notes
- Both changes go into the base launch (`cmd` and `env` are built before the retry loop). They therefore apply to every attempt, every agent class, and both resumed and fresh sessions, as the spec requires. The plan explicitly rules out adding them later with `cmd.extend`.
- The test asserts on position (`cmd[cmd.index("--disallowedTools") + 1]`), not just membership. A regression that separates the flag from its value would fail the test.
- The plan names every launch site the change must not touch and gives a reason for each, so the implementer does not have to guess the blast radius.
- The new test has a docstring that describes behaviour and contains no task or phase numbers.

PLAN_REVIEW_PASS
