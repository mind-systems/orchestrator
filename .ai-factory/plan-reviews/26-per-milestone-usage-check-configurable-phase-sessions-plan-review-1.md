# Plan Review: Per-milestone usage check + configurable phase sessions

**Plan:** `26-per-milestone-usage-check-configurable-phase-sessions.md`
**Risk Level:** 🟢 Low

## Verification Against Codebase

I verified every concrete claim in the plan against `orchestrator/main.py`, the spec note
(`11-usage-guard-and-phase-session-config.md`), the docs, and the ROADMAP entry.

- **Line references are correct.** `_parse_usage_pct()` is lines 29–36; `UsageGuard` is lines
  39–74. Both deletions land exactly where the plan says.
- **`import math` is safe to remove.** `math` is referenced only at line 73 (`math.ceil` inside
  `UsageGuard._predict_next`). After deleting `UsageGuard`, no other reference remains — confirmed
  by grep. The plan's "verify `math` is referenced nowhere else first" instruction is satisfied.
- **`_parse_usage_pct` has no other consumer.** Only `UsageGuard.check` calls it, so deleting both
  together is clean.
- **Loop wiring is correct.** In both `_implement_loop` (708–721) and `_test_loop` (667–680), the
  `threshold = ...` / `guard = UsageGuard(...)` setup and the `guard.check(i)` call sit exactly
  where the plan describes. Replacing `guard.check(i)` with `_check_usage_limits()` after the
  `state.stop_requested` check preserves "runs before every milestone including the first."
- **`PipelineStopError` propagation is preserved.** The new function raises the same exception type
  that `UsageGuard.check` raised; it bubbles through `_with_caffeinate` and is caught in `cli()`.
  No behavioral regression in stop handling.
- **Phase-session branching is sound.** The `elif not phase_sessions_enabled: phase_session_id =
  None` addition correctly forces a reset within the same section while leaving the cross-section
  reset intact. Default `"true"` keeps existing behavior unchanged.
- **File paths are correct.** `docs/configuration.md` and `docs/how-it-works.md` both exist; the
  referenced sections (`### ORCHESTRATOR_USAGE_THRESHOLD`, `## Лимит использования сессии`, `## Фазы
  роадмапа и сессии планировщика`) are present and in Russian, matching the "keep prose in Russian"
  instruction.
- **Roadmap linkage is correct.** This plan maps directly to ROADMAP.md line 67, and faithfully
  implements all three parts of that milestone description.

## Context Gates

- **Architecture (WARN → none):** Change is confined to `orchestrator/main.py` plus two doc files,
  consistent with the file-based, single-module orchestration design in ARCHITECTURE.md. No
  boundary violations.
- **Rules:** No `.ai-factory/RULES.md` present — skipped.
- **Roadmap (OK):** Milestone is present and unchecked; plan scope matches it exactly.

## Observations (non-blocking)

These do not block implementation but are worth keeping in mind:

1. **`/usage` regex relaxation is an intentional change, not just a refactor.** The old session
   pattern was `r"Current session:\s+(\d+(?:\.\d+)?)%\s+used"` (note the trailing `\s+used`). The
   new pattern in the spec drops `used`: `r"Current session:\s+(\d+(?:\.\d+)?)%"`. The new weekly
   pattern `r"Current week \(all models\):\s+(\d+(?:\.\d+)?)%"` is brand new. Neither pattern could
   be validated against live `claude /usage` output from the repo (no fixture exists). Since the
   whole feature hinges on these matching the real CLI output, the implementer should eyeball the
   actual `/usage` text once during implementation. The fail-safe (parse failure → warn/continue)
   means a mismatch degrades gracefully rather than crashing, so this is low-risk.

2. **Silent no-match case.** The spec's `_check_usage_limits` snippet has no try/except; the plan
   correctly adds one (good — more robust than the spec). But note the resulting behavior: if
   `subprocess.run` *succeeds* yet neither pattern matches (e.g. the output format shifted), `parts`
   is empty, nothing prints, and the function returns without any warning. Only a thrown exception
   triggers the `[usage check: could not parse output, continuing]` warning. This is acceptable
   fail-safe behavior, but it's slightly less visible than the old guard, which always printed on
   parse failure. Consider printing the warning when *both* percentages are `None` too — minor.

3. **`_run_loop` is already fully dead code.** Neither `_implement_loop` nor `_test_loop` calls
   `_run_loop` (both use their own inline `for` loops); grep finds zero callers. The plan removes
   only the `before_each` parameter and "leaves the rest intact," which is fine and harmless — but
   the entire function could be deleted instead. Keeping it is a defensible choice; just be aware
   the plan's framing ("the inline loops call `_check_usage_limits()` directly and `_run_loop` is
   the only consumer of `before_each`") slightly understates that `_run_loop` itself is unused.

## Conclusion

The plan is accurate, scoped tightly to the right files, correct about line numbers, deletions,
imports, env-var names/defaults, and loop placement. The three observations above are minor and
non-blocking; the most important one (regex vs. live `/usage` output) is mitigated by the
parse-failure fail-safe already specified. Safe to implement.

PLAN_REVIEW_PASS
