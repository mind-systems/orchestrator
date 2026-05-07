## Code Review: Resume from mid-milestone failure in implement mode

**Files reviewed:** `orchestrator/main.py` (diff + full file)

### Critical Issues

#### 1. `git status --porcelain` matches `.ai-factory/` plan artifacts — skips implementation entirely

Detection step 4 checks whether the working tree is clean using both `git diff HEAD` and `git status --porcelain`. When a previous run completed planning + plan review but crashed before implementation, the `.ai-factory/plans/` and `.ai-factory/plan-reviews/` files are new untracked files in the working tree. `git status --porcelain` reports them (e.g. `?? .ai-factory/plans/10-foo.md`), so step 4 does not match. Detection falls through to step 5 ("no review files") → returns `("review", 1)`.

In `process_milestone`, `("review", 1)` causes the first implement loop iteration to skip `implementer.implement()` entirely (the `step == "review" and iteration == counter` guard). The reviewer then evaluates plan artifacts with no code changes — and may pass, marking the milestone done without any implementation.

Trace with `max_iterations=3`:
1. Previous run: plan created, plan-review-1 passes, crash before implement
2. Resume: detection reaches step 4
3. `git diff HEAD` → empty (plan artifacts are untracked)
4. `git status --porcelain` → `?? .ai-factory/plans/10-foo.md` + `?? .ai-factory/plan-reviews/10-foo-plan-review-1.md`
5. Step 4 fails → step 5: no review files → `("review", 1)`
6. Implement loop: skips implement on first iteration, runs review on zero code changes

**Fix:** Exclude `.ai-factory/` from both git checks in `_detect_milestone_step` using pathspec excludes:
```python
diff = subprocess.run(
    ["git", "diff", "HEAD", "--", ".", ":!.ai-factory"],
    cwd=project_dir, capture_output=True, text=True,
)
status = subprocess.run(
    ["git", "status", "--porcelain", "--", ".", ":!.ai-factory"],
    cwd=project_dir, capture_output=True, text=True,
)
```
Only changes outside `.ai-factory/` should count as evidence that implementation has started. Plan artifacts, plan-review files, review files, and patches all live inside `.ai-factory/` and must be ignored by this check.
