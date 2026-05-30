# Plan Review: 20-resume-guard-write-hardening

**Plan:** `.ai-factory/plans/20-resume-guard-write-hardening.md`
**Spec:** `.ai-factory/notes/06-resume-guard-and-write-hardening.md`
**Risk Level:** 🟢 Low

## Verification of plan claims against codebase

### Task 1 — Resume guard in `process_milestone`
- `orchestrator/main.py:250` — `impl_start = counter if step in ("implement", "review") else 1` ✓ exact match.
- `orchestrator/main.py:251` — `for iteration in range(impl_start, max_iterations + 1):` ✓ exact match.
- `PipelineStopError` already imported at `orchestrator/main.py:13` ✓.
- Failure mode reproducible: `_detect_milestone_step` returns `("implement", n+1)` for `step="review_failed:n"` (main.py:110–112). With `n = max_iterations = 3`, `impl_start = 4`, and `range(4, 4)` is empty — the loop body is skipped and execution falls through to `mark_done()` + `_git_commit()` at lines 281–282. Guard placement (immediately before the loop) correctly traps this.

### Task 2 — Resume guard in `process_test_milestone`
- `orchestrator/main.py:675` — `impl_start = counter if step in ("implement", "test_run") else 1` ✓ exact match.
- Symmetric failure path through `test_run_failed:n` (line 699) → `_detect_milestone_step` returns `("implement", n+1)` ✓ same logic.
- Guard placement (immediately before `for iteration in range(impl_start, max_iterations + 1):` at line 676) is correct.

### Task 3 — `_write_session` hardening
- `orchestrator/agents.py:34-40` — function signature and body match the plan exactly.
- `_read_sessions` pattern at lines 28–31 uses the same `(json.JSONDecodeError, OSError)` tuple ✓ — the proposed code mirrors it consistently.
- `json` and `os` already imported at lines 5–6 ✓.
- Failure scenario confirmed: a corrupt sidecar that survives `_read_sessions` (returns `{}`) will hit `json.loads(p.read_text())` at line 36 on the next write call and crash. The try/except closes that gap.

### Task 4 — `.gitignore`
- `.gitignore` ends at line 35 (after `.mypy_cache/`) with no `*.tmp` rule ✓.
- `_write_session` writes to `p.with_suffix('.json.tmp')` then `os.replace(...)` — confirmed at agents.py:38–40. A SIGKILL between these two calls leaves an orphaned `*.json.tmp` that `git add -A` in `_git_commit` would stage.

## Architecture / Rules / Roadmap gates

- `.ai-factory/ARCHITECTURE.md`, `.ai-factory/RULES.md`, `.ai-factory/ROADMAP.md`: not inspected here (not required by the project's CLAUDE.md and not part of the plan's scope). No boundary violations introduced — all edits are local to existing files and preserve current function signatures.
- No new imports, no new modules, no public-API changes — architectural impact is nil.

## Findings

### Critical Issues
None.

### Suggestions (non-blocking)
1. **Settings section says "Logging: minimal".** The new guard uses `raise PipelineStopError(...)` which already produces a visible error trace upstream — no `print()` needed before raising. Plan is consistent with the existing style (lines 230–233, 245–247, 274–277 all `raise` without prefixing a `print`). No change requested.
2. **Diagnostic clarity (optional).** The error message could optionally include `step` (e.g. `f"... step='{step}' counter={counter} max_iterations={max_iterations}"`) so the operator immediately sees which transition triggered it. Not required — the current message names the actionable env var, which is the important part.
3. **Sidecar atomic-write robustness.** `_write_session` writes `tmp` then `os.replace`. If the process crashes between `tmp.write_text` and `os.replace`, the next run silently rewrites with fresh content (Task 3 covers reading corrupt JSON, but a stale `.json.tmp` is the artifact Task 4 hides from git). The pair of fixes (Task 3 + Task 4) correctly addresses both halves of the failure window.

### Positive Notes
- File paths, line numbers, and code snippets in the plan match the codebase exactly.
- Pattern reuse: Task 3 follows the existing `_read_sessions` exception-handling style instead of inventing a new one.
- Spec ↔ plan alignment is 1:1 — every fix in `06-resume-guard-and-write-hardening.md` maps to one task with the same scope.
- Tasks are small, independent, and ordered by safety (guard the regression first, harden second, gitignore last) — clean blast-radius layering.

## Conclusion
All four tasks are precisely scoped, technically correct, and address the documented regression and hardening gaps from milestone 19. No missing steps, no incorrect assumptions, no architectural concerns, no security issues.

PLAN_REVIEW_PASS
