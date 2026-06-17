# Plan Review: Adaptive session usage guard

**Plan:** `.ai-factory/plans/25-adaptive-session-usage-guard.md`
**Target:** `orchestrator/main.py`
**Risk Level:** 🟢 Low

## Verification Summary

I verified every concrete claim in the plan against the codebase:

- `PipelineStopError` **is** imported at `main.py:13` ✅
- `re` and `math` are **not** imported (only `argparse`, `os`, `signal`, `subprocess`, `sys`, `time`, `pathlib`) ✅
- `import os` is present (`main.py:6`) — env-var read in Task 5 is sound ✅
- `_implement_loop` (line 627) and `_test_loop` (line 590) both iterate inline with `for i, milestone in enumerate(pending, start=_next_number(plans_dir))` and check `state.stop_requested` — they do **not** call `_run_loop` ✅. The plan's "Notes for implementer" correctly reconciles this; the note's "Wiring into loops" section (which claims both loops call `_run_loop`) is misleading, but the plan overrides it correctly.
- The loops reference `state.stop_requested` (module imported as `from . import state`), not `_state`. The plan tasks say "after the `state.stop_requested` check" — **correct**. (The note's pseudocode uses `_state.stop_requested`, which would be wrong; the plan does not repeat that mistake.)
- `PipelineStopError` propagation path is real: `guard.check(i)` raises → propagates through `_implement_loop`/`_test_loop` → `_with_caffeinate` (catches `Exception`, prints elapsed, re-raises) → `cli()` catches `PipelineStopError` and exits 0. No extra try/except needed, as the plan states ✅.

### Index semantics — confirmed correct

The `i` passed to `guard.check(i)` is **not** a 0-based milestone index — `enumerate(pending, start=_next_number(plans_dir))` starts it at the next plan-file number (e.g. 26). This is fine: `_predict_next` only uses *differences* of `idx` (`span = idx - history[0][0]`, `avg_delta = delta_pct / span`) and `idx` still increments by exactly 1 per iteration, so the algorithm is offset-invariant. `UsageGuard` is constructed fresh inside each loop with `_next_check_at = 0`, so the first milestone always checks regardless of the starting offset. No bug here.

## Context Gates

### Architecture (`.ai-factory/ARCHITECTURE.md`) — WARN
ARCHITECTURE.md lists an explicit anti-pattern (line 103):

> ❌ Calling the `claude` CLI directly from `main.py` — only via agent classes in `agents.py`

Task 2's `_parse_usage_pct()` runs `subprocess.run(["claude", "/usage"], ...)` **directly from `main.py`**, which technically crosses this documented boundary. The dependency rules also say agent/CLI concerns live in `agents.py`.

This is **non-blocking**: the note deliberately scopes the work to `main.py` only, and the guard is orchestration-level control flow (not an LLM agent that manages a `session_id` / sidecar). Cleaner would be a thin `agents.py` helper (e.g. `read_session_usage()`) called from the guard, keeping the `claude` invocation in the agent layer. Recommend either following that boundary or adding a one-line note to ARCHITECTURE.md acknowledging the guard as an allowed exception. Not required for this milestone.

### Rules (`.ai-factory/RULES.md`) — WARN
No `RULES.md` present. No explicit convention violations detectable.

### Roadmap (`.ai-factory/ROADMAP.md`) — pass
ROADMAP.md exists; this is a `feat`-shaped change with a corresponding milestone. Linkage present.

### Skill-context — pass
No `.ai-factory/skill-context/aif-review/SKILL.md` present; default rules apply.

## Non-blocking Observations

1. **`_run_loop` is dead code.** It is defined at `main.py:27` but never called anywhere in the package (verified by grep). Task 4 ("add `before_each` hook to `_run_loop`") therefore modifies an unused function — harmless forward-compatibility, but the implementer should be aware it has no runtime effect today. The real wiring is Task 5 (inline `guard.check(i)`), which is what matters. The plan already flags this duality in its notes — good.

2. **Core functional assumption — `claude /usage` output (key validation risk).** The whole feature hinges on `subprocess.run(["claude", "/usage"])` (a) running non-interactively at all and (b) printing `Current session: N% used` to **stdout**. `/usage` is normally an interactive REPL slash-command; its non-interactive stdout format is unverified, and TUI output often carries ANSI escape sequences / box-drawing that could break the regex `r"Current session:\s+(\d+(?:\.\d+)?)%\s+used"`. The note's own "Open Questions" flags the latency angle but not the format. The graceful-degradation design (return `None` → print "could not parse" → re-check in 5) means a permanent parse-miss fails **open**: the pipeline runs *unguarded* and silently. This is acceptable as designed (the guard is best-effort) but the implementer should manually run `claude /usage` once and confirm the regex matches; if it doesn't, the feature is a no-op. Consider stripping ANSI (`re.sub(r"\x1b\[[0-9;]*m", "", stdout)`) before matching as cheap insurance.

3. **Cosmetic rounding.** `print(f"  [usage: session {pct:.0f}% used]")` rounds for display, so a `pct` of 89.6 prints "90% used" while *not* stopping (89.6 < 90.0 threshold). Minor log confusion only; logic is correct.

4. **Defensive subprocess wrapping (Task 2).** Catching broad `Exception` to return `None` is correct here and matches the "never crash the pipeline" requirement. `timeout=30` is reasonable given the note warns `claude /usage` spawns a full session.

## Verdict

The plan is internally consistent, all codebase claims check out, the algorithm is correct (including the non-zero index offset), the error-propagation path is real, and no migrations or security concerns apply. The only issues are an architectural boundary WARN (CLI call from `main.py`) and the inherent `claude /usage` output assumption — both non-blocking and both with the design failing open rather than crashing. No missing steps.

PLAN_REVIEW_PASS
