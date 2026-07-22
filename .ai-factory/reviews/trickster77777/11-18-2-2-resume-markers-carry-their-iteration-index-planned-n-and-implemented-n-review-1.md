# Review: 18.2.2 — Resume markers carry their iteration index — `planned:N` and `implemented:N`

## Scope reviewed
`git diff HEAD` — three source files:
- `orchestrator/resume.py` — `_validate_sidecar_step` + `_detect_step` dispatch.
- `orchestrator/main.py` — three marker writes in `process_task`.
- `tests/test_main.py` — one fixture update.

Read each changed file in full (plus the plan, the governing spec `32-resume-carries-verify-iteration.md`, the 18.2.1 grammar tests, `docs/how-it-works.md`, and the sibling `task-rescue`/`orchestrator-artifacts` skills).

## Verification

**`resume.py` — validation.** The bare `("planned", "implemented")` always-valid branch is removed and replaced by a `startswith("planned:") | startswith("implemented:")` branch that parse-guards the ordinal with `int(step_value.split(":")[1])` and returns `""` on `IndexError`/`ValueError` (`planned:abc`, `planned:` → cleared). No artifact-existence stat, matching the structural-validity contract. Prefix collisions checked and clear: `"plan_review_failed:1"` does not start with `"planned:"` (diverges at index 4: `_` vs `n`), so its own later branch still owns it; `"implemented:1"` shares no prefix with `review_failed:`/`test_run_failed:`. Docstring updated to match.

**`resume.py` — dispatch.** `planned:N` → `("plan_review", N)` and `implemented:N` → `(verify_step, N)`, parsing `N` the same way. Branch order is safe: `planned:` is tried first but matches neither `plan_review_failed:` nor `plan_reviewed`, so those keep their exact-match branches. Single dispatch site — `_detect_task_step` (review) and `_detect_test_task_step` (test_run) inherit it, so test mode is covered by construction.

**`main.py` — writes.**
- L277 `f"planned:{counter}"` — I confirm the plan's DEVIATION from the spec's literal `planned:1` is correct, not a regression. This line is re-hit on resume from `("plan", N+1)` (crash inside the re-plan) where `counter = N+1 > 1`; a literal `1` there would let a subsequent crash resume as `("plan_review", 1)`, re-reviewing attempt 1 against the attempt-(N+1) plan and overwriting `plan-review-1.md` — the exact bug class this task removes. `counter` is always ≥ 1 on this path (fresh = 1, or `n+1` ≥ 2), and byte-identical to `planned:1` in the fresh case. Upholds the `how-it-works.md` invariant "planned:N names round N".
- L306 `f"planned:{attempt + 1}"` — correctly placed as the last statement of the `for attempt` loop body, reached only after `plan_review_failed:{attempt}` (L301) and the re-plan (L302–305), i.e. only when the review failed and `attempt < max_iterations`. Records the revised plan for attempt N+1 so a crash during plan-review N+1 resumes at `("plan_review", N+1)` with no planner re-run. The `plan_review_failed:{attempt}` write is retained to guard the crash-during-re-plan window.
- L329 `f"implemented:{iteration}"` — serves both `review` and `test_run`; the implement-loop guard (`iteration == counter`) and the `max_iterations` guard are untouched, so on resume `impl_start = N`, implement short-circuits, `review-N.md` is written fresh, `review-(N-1).md` read as prior.

**Reasoning traces reproduce the spec's Verify section.** `implemented:3` → `("review", 3)`; `planned:2` → `("plan_review", 2)` (no planner run); `plan_review_failed:1` → `("plan", 2)` (re-plan). All hold.

**Tests.** `uv run pytest` → **191 passed**. The 18.2.1 grammar assertions now pass through the explicit `planned:`/`implemented:` branches (not the heuristic): each fixture writes only the sidecar `step` with no plan-review/review files that would let the heuristic coincidentally produce the same tuple — e.g. `implemented:3` with no reviews would heuristic to `("plan_review", 1)`, so `("review", 3)` can only come from the explicit branch. The one pre-existing bare-`implemented` fixture (`test_detect_task_step_subdird_dirs_dispatches_same_as_flat`) is correctly migrated to `implemented:1`; the surviving bare-`"planned"` adoption/survivor fixtures remain green via the heuristic (they exercise git-adoption, not marker grammar).

**Herald migration.** `/Users/max/projects/repo-stats-herald/.ai-factory/plans/34-6-2-coordination-root-seeding.json` reads `"step": "implemented:3"` — already migrated; verified, no action needed.

No stray readers of the bare markers remain in the orchestrator package (only a stale `.pyc` matched).

### Critical Issues
None.

### Positive Notes
- The `planned:{counter}` correction (over the spec's literal `planned:1`) is the sharp call in this task and it is right — it closes the plan-side twin of the very bug the task targets, and the reasoning is documented at the site in the plan.
- The dispatch is genuinely explicit, not heuristic-coincident: the tests would not pass on the fallback path, so the grammar contract is actually enforced.

## Deferred observations
- Affects: `skills/.ai-factory/specs/trickster77777/83-task-rescue-indexed-sidecar-markers.md` — This diff completes the orchestrator half of the clean break, but the sibling `task-rescue` skill (`skills/src/skills/task-rescue/SKILL.md`) is still the one skill-side writer of the sidecar `step` and it both writes and documents the retired **bare** `"planned"`/`"implemented"` forms (rollback procedures :304/:323, Emit lines :310/:326, the closed-set grammar table :360/:363, and the "always-valid" guards). After this task a bare marker passes validation but matches no `_detect_step` branch and degrades to the disk heuristic. The interim is runtime-safe — task-rescue deletes *all* plan-reviews (spec+plan depth) or *all* reviews (spec+plan+code depth) before writing, which steers the heuristic to the identical target (`("plan_review",1)` / `("review",1)` respectively) — so nothing breaks before the skills side lands. The paired reconciliation is already scoped as skills task 83 (migrate the writes to `planned:1`/`implemented:1` and re-sync the grammar table); no orchestrator action is required, but the skills task must ship to remove the documented-grammar drift and stop emitting values the orchestrator no longer dispatches explicitly. Out of this task's file boundary (sibling repo), hence deferred rather than a finding.

REVIEW_PASS
