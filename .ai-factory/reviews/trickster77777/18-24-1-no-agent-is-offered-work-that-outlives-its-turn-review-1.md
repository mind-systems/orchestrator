## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/agents.py`, `tests/test_agents.py`)
**Risk Level:** 🟢 Low

### Context Gates
- Architecture: OK — the change stays inside `_run_claude` in `agents.py` and adds no new imports (`os` was already imported); layer rules in `.ai-factory/ARCHITECTURE.md` are untouched.
- Rules: `.ai-factory/RULES.md` is absent — WARN (no project rules to check against).
- Roadmap: OK — the diff implements 24.1 in `.ai-factory/roadmaps/trickster77777.md` exactly as its task spec `0057-no-work-outlives-the-turn.md` pins: `--disallowedTools` plus the literal `Monitor,ScheduleWakeup,CronCreate` in the base `cmd` list right after the `--allowedTools` pair, and `env={**os.environ, "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}` built before the retry loop and passed to `Popen`. The governing spec (`docs/pipeline.md` § Agent sessions) already states this behaviour, so no doc change is needed.
- Guard: `--allowedTools`, the default `allowed_tools` list, and every agent's `tools` list are unchanged. `usage.py`'s `claude /usage` call and `runtime.py`'s `caffeinate` launch are untouched, as the spec requires.

### Critical Issues
None.

Verification:
- The variadic `--disallowedTools` is always followed by another flag (`--model`, `--effort`, `--resume`, `--system-prompt`) or by the end of `cmd`. The prompt sits earlier as the value of `-p`, so nothing can be swallowed into the deny list.
- `cmd` and `env` are both built before the `for attempt` loop, so every retry reuses them. The new flag is in the base list, so it applies to resumed and fresh sessions alike.
- Merging `os.environ` keeps the inherited environment (PATH, auth, and so on), and the override wins because it comes last in the dict literal.
- The new test runs the real success path: `_classify_result` returns `ok`, and `_run_claude` returns normally. It then pins both the env var and the element that immediately follows `--disallowedTools`. The existing rate-limit test's `lambda *a, **kw` still accepts the new `env` keyword. The full suite passes (`uv run pytest`: 221 passed).

### Positive Notes
- This is the smallest change that could work. It matches the spec exactly and adds no incidental edits or comments.
- The test follows the existing `_FakeRateLimitProc` pattern and uses the `clean_active_proc` fixture. Its name and docstring describe the behaviour rather than a task number.

REVIEW_PASS
