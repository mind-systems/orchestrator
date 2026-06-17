# Code review: Per-milestone usage check + configurable phase sessions

## Scope
Reviewed `git diff HEAD` against the plan. Changed files:
- `orchestrator/main.py` — replaced `_parse_usage_pct` + `UsageGuard` with `_parse_pct` + `_check_usage_limits`; removed `before_each` from `_run_loop`; removed `import math`; wired the check and `ORCHESTRATOR_PHASE_SESSIONS` into `_implement_loop` and `_test_loop`.
- `docs/configuration.md` — env-var table rows + section rewrites.
- `docs/how-it-works.md` — two section rewrites.

Read the full updated `main.py` and surrounding loop code; grepped the whole package for stale references.

## Verification

- **No dangling references.** Grep over `**/*.py` for `UsageGuard`, `_parse_usage_pct`, `before_each`, `math`, `_run_loop` returns only the `_run_loop` definition itself. The removed symbols are gone everywhere; `import math` was the sole `math` user and is correctly dropped. Remaining hits live only in old review/roadmap markdown, not code.
- **`before_each` removal is safe.** `_run_loop` has zero callers (confirmed by grep), so dropping its `before_each` parameter breaks nothing. It was already dead code before this change — not a regression.
- **`_check_usage_limits` logic is correct.** Subprocess wrapped in `except Exception` (not `BaseException`), so `KeyboardInterrupt`/`SystemExit` still propagate and Ctrl+C during a usage check works. `subprocess.run` is called without `check=True`, so a nonzero `claude` exit with usable stdout still parses. Parse failure → log + return, never crash. Both thresholds are checked independently; each `None` pct is skipped, matching the documented "ignored if not returned" behavior.
- **Dual-print branch is sound.** When the subprocess succeeds but neither regex matches, `parts` is empty → prints the "could not parse" line and returns before any threshold comparison. No spurious stop, no double log on the success path.
- **Regex relaxation is intentional and safe.** Session pattern dropped the trailing `\s+used` from the old version; both new patterns capture `(\d+(?:\.\d+)?)%` and feed `_parse_pct`, which returns `None` on no match. Output format `[usage: session 26% · week 52%]` matches the spec example.
- **Phase-session gating is correct.** `phase_sessions_enabled = ...lower() != "false"` (default carries forward). The branch resets `phase_session_id` on section change, and additionally on every milestone within a section when disabled — exactly the spec's A/B semantics. First-iteration behavior with `current_section=None` (sectionless roadmap) is unchanged from prior code: no reset, so a single phase session is shared, preserving existing behavior.
- **Stop path intact.** `PipelineStopError` raised from `_check_usage_limits` propagates through `_with_caffeinate` (re-raises after printing elapsed) to `cli()`'s `except PipelineStopError` → clean exit 0. Identical handling to the prior guard.
- **Both loops updated identically.** `_implement_loop` and `_test_loop` received the same edits; the check runs after the `state.stop_requested` guard and before section handling, so it fires before every milestone including the first.

## Observations (non-blocking, pre-existing — no action required)

- `_run_loop` remains unused dead code. It predates this change and the prior review already noted it; out of scope here.
- `float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", ...))` is unguarded against a non-numeric env value (would raise `ValueError`). This matches the prior implementation (it parsed the same env var unguarded at loop start); the only change is that parsing now happens inside the check per milestone rather than once. Not a regression.

## Docs
Both doc files are accurate to the new behavior, keep Russian prose consistent with neighbors, add the two new env rows with correct defaults (95 / true), remove the adaptive/prediction description, and document the dual thresholds, the `[usage: ...]` log line, the parse-failure fail-safe, and the `ORCHESTRATOR_PHASE_SESSIONS=false` A/B use.

No correctness, security, or runtime issues found.

REVIEW_PASS
