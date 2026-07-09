## Plan Review Summary

**Plan:** Tests-first: alert colour mapping + `cli()` exception routing
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): No boundary/dependency concern — the plan only adds/extends files under `tests/`, an existing surface. No production module is touched. OK.
- **Rules** (`.ai-factory/RULES.md`): absent — WARN, non-blocking (nothing to enforce).
- **Roadmap alignment**: The plan's `# Plan:` heading matches `ROADMAP.md` line 33 ("Tests-first: alert colour mapping + `cli()` exception routing"). The milestone lives in **ROADMAP.md (implement mode)**, not ROADMAP_TESTS.md — so it is gated on `PlannerReviewer.review()` (REVIEW_PASS), *not* on a real `TestRunner` run. This is the key reason "red by design" is safe here: no green test-gate blocks the milestone, and the plan correctly omits a `## Test Command` section (which would only matter in `test` mode). The `Spec:` note `.ai-factory/specs/07-notify-routing-tests.md` was read and the plan matches it clause-for-clause (emoji mapping, gating no-ops, `cli()` routing incl. re-raise, source-level `HaltError` re-pointing, and the "what NOT to test" exclusions). Alignment confirmed.

### Critical Issues
None.

### Verification against the actual code
Every load-bearing assumption in the plan was checked against source:

- **Task 1 (emoji mapping):** `notify.py:24` currently does `"🔴" if alert_type in _FAIL_ALERTS else "🟢"`, with `_FAIL_ALERTS = {"stop"}`. So `stop`→🔴, and `halt`/`milestone`/`done`/unknown all →🟢 today. The plan's green-now / red-now split (halt is the sole red-by-design case) is exactly right.
- **Task 2 (gating):** The two guards at `notify.py:20-23` (`alert_type not in telegram_alerts`; falsy token/chat_id) match the three no-op cases the plan pins. All green now.
- **Task 3 (`cli()` routing):** `cli()` (`main.py:762-796`) references `load_config`, `run_implement`, `notify` as module globals — all monkeypatchable via `orchestrator.main.*`. `except RateLimitError` currently records `"stop"` (`main.py:795`) → correctly "red now" for the `"halt"` assertion. There is no `except Exception` today, so a generic `ValueError` propagates while `notify` never fires → the plan's clean-AssertionError red (inside `pytest.raises(ValueError)`) is accurate, not a collection error. `sys.exit(0)` raising `SystemExit` for the `PipelineStopError`/`RateLimitError` paths is correct. The decision to exercise the halt family through the concrete `RateLimitError` (already defined at `agents.py:69`) rather than naming the not-yet-existent `HaltError` is sound.
- **Task 4 (source exception types):**
  - Usage breach: `_check_usage_limits` reads `subprocess.run(...).stdout`, parses `Current session:\s+(\d+…)%`, and raises `PipelineStopError` at `main.py:63` when `session_pct >= threshold`. Stubbing `orchestrator.main.subprocess.run` to return `.stdout="Current session: 99%"` with `usage_threshold_5h=90` deterministically hits that raise; the weekly pattern won't match so only the session branch fires. Correct, and no `claude` call.
  - Resume-past-max: traced `process_milestone(tmp_path, milestone, 1, config)` with sidecar `{"step":"review_failed:3"}` + `reviews/01-slug-review-3.md` + passing `plan-reviews/01-slug-plan-review-1.md`, `max_iterations=3`. `_detect_milestone_step` takes the sidecar branch (`main.py:213-215`) → `("implement", 4, plan_path)` and returns *before* the git-subprocess heuristic (steps 5-7), so no git repo is needed — the plan's claim holds. The safety guard at `main.py:349` passes precisely because the passing plan-review exists (this is why the plan includes it), so execution reaches `impl_start = 4` and raises at `main.py:356` (`4 > 3`) — currently `PipelineStopError`, red until 05. Confirmed the raise precedes every `_run_claude`/git call.
- **Agent construction in the Task 4 resume test:** `PlannerReviewer`/`Implementer` constructors run before the `main.py:356` raise. Verified they only call `_load_prompt(name)`, which reads packaged prompt files under `PROMPTS_DIR` (relative to the module, not `tmp_path`) — no network, no subprocess, no git. So "pure object construction" is accurate; the constructed agents never reach `_run_claude`.
- **`HaltError` dynamic-fetch idiom:** `HaltError` does not exist in `agents.py` today (only `RateLimitError`, `PipelineStopError`). The plan's `getattr(agents, "HaltError", None)` + `assert HaltError is not None` keeps the module importable (no top-level `ImportError`), turning the collection-safe red into a clean assertion. Correct.
- **Line-number references** (`main.py:348/356`, `main.py:63,67`) map accurately onto the current source and onto task 05's declared change sites in `ROADMAP.md` line 35.

### Positive Notes
- The plan is scoped strictly to silent-failure surfaces (colour mapping, alert-type routing, source exception *type*) and explicitly excludes loud/non-deterministic surfaces (real HTTP, agent LLM calls, git, signal wiring) — faithful to `test-philosophy` and the spec's "what NOT to test".
- The green-now vs red-by-design boundary is called out per assertion, so the reviewer of the resulting code can distinguish an intended TDD red from a regression.
- Deterministic stubbing throughout (recorder for `send_telegram`/`notify`, stubbed `subprocess.run`, `OrchestratorConfig` built directly rather than via `load_config()`) keeps the suite hermetic.
- Reuse of the existing `_dms_dirs` fixture pattern and single-function-per-case style matches the current `tests/test_main.py` conventions.

### Minor (non-blocking) note for the implementer
- `OrchestratorConfig` has four required fields with no defaults (`max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`). The per-test config helpers must supply all four even when a test only cares about one (e.g. the usage test cares about `usage_threshold_5h`, the resume test about `max_iterations`). The plan's "Key constraints" already points at the dataclass, so this is just a reminder, not a gap.

PLAN_REVIEW_PASS
