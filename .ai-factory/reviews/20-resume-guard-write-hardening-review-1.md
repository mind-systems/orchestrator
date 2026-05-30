# Code Review: 20-resume-guard-write-hardening

**Plan:** `.ai-factory/plans/20-resume-guard-write-hardening.md`
**Spec:** `.ai-factory/notes/06-resume-guard-and-write-hardening.md`

## Scope of changes

- `orchestrator/main.py` — two `PipelineStopError` guards (lines 251-255, 681-685)
- `orchestrator/agents.py` — `_write_session` internal read wrapped in `try/except (JSONDecodeError, OSError)` (lines 36-39)
- `.gitignore` — `*.json.tmp` rule appended (lines 37-38)
- `.ai-factory/ROADMAP.md` — milestone entry added (queued, not done)
- `.ai-factory/notes/06-…md`, `.ai-factory/plans/20-…md`, `.ai-factory/plan-reviews/20-…md`, `.ai-factory/plans/20-…json` — orchestrator artifacts

## Verification against plan and codebase

### Task 1 — `process_milestone` guard
`orchestrator/main.py:251-255` matches the plan verbatim. Placement is correct: immediately after `impl_start = counter if step in ("implement", "review") else 1` and before `for iteration in range(impl_start, max_iterations + 1):`.

Reproduced the failure path manually:
- `_detect_milestone_step` at lines 110-112 returns `("implement", n+1)` for `step="review_failed:n"`.
- With `n = max_iterations = 3`, `counter = 4`, `impl_start = 4`, `range(4, 4)` is empty.
- Pre-fix: execution would skip the loop, fall through to `mark_done()` + `_git_commit()` at lines 285-286.
- Post-fix: `4 > 3` → `PipelineStopError`, caught in `cli()` at line 906 → graceful stop. ✓

`PipelineStopError` is already imported at line 13 of `main.py`. No new import needed.

### Task 2 — `process_test_milestone` guard
`orchestrator/main.py:681-685` mirrors Task 1 exactly, placed after `impl_start = counter if step in ("implement", "test_run") else 1` (line 680). Symmetric failure path through `step="test_run_failed:N"` at line 703 is fully covered. ✓

### Task 3 — `_write_session` hardening
`orchestrator/agents.py:34-43` matches the plan and mirrors `_read_sessions`'s exception tuple `(json.JSONDecodeError, OSError)`. `json` and `os` are imported at lines 5-6. The corrupt-sidecar regression (sidecar survives `_read_sessions` → returns `{}` → first `_write_session` crashes on `json.loads`) is now neutralized: the same path now silently rewrites the file with fresh content. ✓

### Task 4 — `.gitignore`
`.gitignore` ends with a new commented section `# Sidecar atomic-write temp files` followed by `*.json.tmp` on a new line, preserving the file's existing comment/section style. A stale `*.json.tmp` left by a `kill -9` between `tmp.write_text` and `os.replace` will no longer be staged by `git add -A` in `_git_commit`. ✓

## Correctness analysis

### Boundary check (`>` vs `>=`)
The guard uses `impl_start > max_iterations`. Boundary table:

| `max_iterations` | `counter` (=`impl_start`) | guard triggers? | loop range | iterations run |
|---|---|---|---|---|
| 3 | 3 | no (3 > 3 false) | `range(3, 4)` | one iteration | ✓ |
| 3 | 4 | yes (4 > 3 true)  | n/a | `PipelineStopError` | ✓ |
| 5 | 4 (after env bump from 3) | no (4 > 5 false) | `range(4, 6)` | iterations 4 and 5 | ✓ |

Boundary is correct — the guard fires only when the loop would otherwise be empty.

### Resume from `step="review"` / `step="test_run"`
`_detect_milestone_step` only returns these steps when the previous iteration completed implementation and stopped mid-review. Since the loop writes `step="implemented"` only inside the loop body (lines 263, 692), and `step="review_failed:N"`/`test_run_failed:N` only after a failed review/test, a `("review", N)` return implies the previous run completed iteration N's implement and was reviewing. N is therefore bounded by the prior run's `max_iterations`. The guard correctly handles the cross-run case where the user shrinks `ORCHESTRATOR_MAX_ITERATIONS` below the persisted counter — it stops gracefully instead of skipping the loop. ✓

### Race-condition surface of `_write_session`
The atomic-write pattern is `tmp.write_text(...)` → `os.replace(tmp, p)`. Failure modes considered:
- Crash before `tmp.write_text` completes: `*.json.tmp` is partial; next `_write_session` overwrites it cleanly (truncating `tmp.write_text` on a fresh handle). Stale tmp is now `.gitignore`d. ✓
- Crash between `tmp.write_text` and `os.replace`: `p` is unchanged, `*.json.tmp` is full and orphaned. Same — ignored by git, overwritten next call. ✓
- `os.replace` itself is atomic on POSIX (same filesystem). No corruption window. ✓
- Concurrent writers: out of scope (orchestrator is single-threaded per project_dir). 

### Exception-tuple symmetry
Task 3 uses the same `(json.JSONDecodeError, OSError)` tuple as `_read_sessions`. `OSError` is technically unreachable inside the `try` (the read is guarded by `p.exists()` and we are the sole writer), but matching the existing pattern is the right call for grep-symmetry and future-proofs against a permission-denied edge case after `chmod`. ✓

## Potential issues considered (and dismissed)

1. **`process_refactor_milestone` also has `impl_start = counter if step in ("implement", "review") else 1`** (line 380). However, `process_refactor_milestone` never writes `step="review_failed:N"` (no `_write_session(..., "step", ...)` call in the verify loop at lines 391-408). The detection function would fall back to the heuristic, which sets `counter = len(review_files) + 1`. The heuristic is itself bounded by what was written in prior runs (max `max_iterations` files), so the empty-range regression can only manifest after a manual sidecar edit. The spec explicitly scopes Fix 1 to two insertion points and notes the milestone-19 regression vector (`review_failed:N`) does not apply to refactor. Not in scope, no defect introduced. (Optional follow-up: unify step-tracking across all three flows in a future milestone.)

2. **Error message wording.** "Bump `ORCHESTRATOR_MAX_ITERATIONS` to continue" names the actionable env var clearly — the user knows exactly what to change. The message does not surface `step`/`counter`/which milestone, but `PipelineStopError`'s `__str__` is printed by `cli()` at line 908 with `STOPPED — {e}` and the prior log line already names the milestone (`MILESTONE: …` banner at line 165). Sufficient diagnostic context.

3. **`.gitignore` placement.** New rule is at end-of-file under a fresh comment header — no interaction with existing sections. ✓

4. **Sidecar committed in this branch.** `.ai-factory/plans/20-resume-guard-write-hardening.json` is staged. This is the orchestrator's own working sidecar for the current milestone — consistent with prior milestones' workflow (sidecars are part of the artifact set, not the temp tmps). Not a defect.

## Findings

### Critical
None.

### Suggestions (non-blocking)
None.

### Positive notes
- All four diffs are minimal and surgical.
- Task 3 reuses the established `_read_sessions` exception pattern instead of inventing a new one — consistent style.
- Guard placement (right after the assignment, before the loop) gives the cleanest stack trace and the smallest semantic surface.
- Boundary check (`>` not `>=`) is correct — verified against the iteration table above.

## Conclusion
All four tasks are implemented exactly as planned. The fix correctly closes the silent-data-loss regression in `process_milestone` and `process_test_milestone`, hardens `_write_session` against corrupt sidecars, and prevents stale tmp files from being committed. No bugs, no missing edges, no architectural concerns, no security issues.

REVIEW_PASS
