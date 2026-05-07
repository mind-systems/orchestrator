## Plan Review: Resume from mid-milestone failure in implement mode

**Files Reviewed:** Plan + 4 source files (main.py, agents.py, roadmap.py, state.py) + previous plan review
**Risk Level:** 🟢 Low

### Context Gates
- `ARCHITECTURE.md` — WARN: file does not exist. No boundary/dependency check possible.
- `RULES.md` — WARN: file does not exist.
- `ROADMAP.md` — Plan aligns with the pending milestone. Detection logic matches the roadmap description.

### Previous Review Issues — Resolution Check

All four issues from plan-review-1 have been addressed:

1. **Counter exceeds max_iterations (was Critical)** — Fixed. Plan now includes a "Plan review safety guard" that reads the latest plan-review file and verifies it ends with `PLAN_REVIEW_PASS` before entering the implement/review loop. Raises `PipelineStopError` if not. This prevents the silent bypass where an empty `range()` lets an unreviewed plan reach implementation.

2. **`git diff HEAD` misses untracked files (was Critical)** — Fixed. Task 1 step 4 now explicitly requires both `git diff HEAD` and `git status --porcelain`, returning `("implement", 1)` only when both produce empty output.

3. **"done" handler skips elapsed time (was Other)** — Fixed. Task 2 explicitly states: "Print elapsed time (record `milestone_start = time.monotonic()` before the detection call), then jump to `mark_done()` + `_git_commit()`, print the elapsed timing line, and return. Do not skip the timing print."

4. **Session context loss unacknowledged (was Other)** — Fixed. Plan adds a top-level "Session context on resume" section acknowledging that agents are created fresh and explicitly stating not to persist session IDs.

### Critical Issues

None.

### Other Observations

#### Plan-review path construction uses counter arithmetic instead of glob

Task 2 (Plan step) says: "find the latest plan-review file (`{seq}-{slug}-plan-review-{counter - 1}.md`)". This constructs the path from `counter - 1`, assuming files are numbered sequentially without gaps. In normal operation this holds (the pipeline creates them sequentially), but it's inconsistent with Task 1's detection logic which uses glob + sort. An implementer could use glob-and-sort here too for robustness, but the current formulation works for all realistic scenarios.

### Positive Notes

- The detection chain (Task 1) is well-ordered — each step depends on the previous one's absence, making it straightforward to reason about correctness.
- The safety guard between plan review and implement/review loops is a clean defensive measure that prevents all bypass scenarios, including the edge case where `counter > max_iterations` produces an empty range.
- The `("done", 0)` fallback correctly handles the narrow crash window between review-PASS and mark_done/commit.
- The plan correctly keeps all flow control in `process_milestone()` — `_detect_milestone_step()` is a pure detection function with no side effects.
- Using existing artifact files for state detection (instead of a new state file) is debuggable — a human can inspect the same files to understand where the pipeline stopped.
- The session context note prevents implementers from attempting session ID persistence, which would add complexity for minimal benefit.

PLAN_REVIEW_PASS
