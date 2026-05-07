## Plan Review: Resume from mid-milestone failure in refactor mode

**Plan File:** `12-resume-from-mid-milestone-failure-in-refactor-mode.md`
**Risk Level:** Low

### Context Gates
- `ARCHITECTURE.md`: not present (WARN — no boundary rules to check against)
- `RULES.md`: not present (WARN — no explicit conventions to validate)
- `ROADMAP.md`: present. Milestone #12 matches plan scope exactly. No misalignment.
- `skill-context/aif-review/SKILL.md`: not present (WARN — no project-specific review rules)

### Approach Validation

The plan correctly identifies that `process_refactor_milestone()` is structurally parallel to `process_milestone()` (both follow plan -> plan_review -> implement -> review/verify -> done). Reusing `_detect_milestone_step()` rather than writing a separate detector is the right call — the returned step names ("plan", "plan_review", "implement", "review", "done") map cleanly to the refactor flow, and the detection logic (check plan file, check plan-reviews, check git diff, check review files) is mode-agnostic.

All six sub-steps follow the established pattern in `process_milestone()` (lines 126-245). The conditional wrapping, counter threading, and resume-skip logic are consistent.

### Findings

**1. Sub-step 2 wording is ambiguous (low risk)**

> "Print the resume message if `step != "audit_and_plan"` (maps from `step != "plan"`)."

`_detect_milestone_step` returns `"plan"`, not `"audit_and_plan"`. The parenthetical clarifies the actual code check, but the primary clause reads like literal code. An implementer could write `if step != "audit_and_plan":` which would always be `True` — printing the resume message on every fresh start. The intended code is `if step != "plan":`, matching `process_milestone` line 148.

Not a logic error in the plan's intent, but the phrasing creates unnecessary ambiguity.

**2. Safety guard between plan review and implement/verify not called out (low risk)**

Current code (lines 299-304) has a safety guard between the plan review loop and the implement/verify loop:

```python
_plan_review_files = sorted(plan_reviews_dir.glob(f"{seq}-{slug}-plan-review-*.md"))
if not _plan_review_files or not _plan_review_files[-1].read_text().strip().endswith("PLAN_REVIEW_PASS"):
    raise PipelineStopError(...)
```

The plan's sub-steps 5 and 6 describe the two loops but don't mention this guard. Since it runs unconditionally (not inside any loop) and the plan only asks to wrap specific blocks in conditions, an implementer following the instructions would naturally leave it in place. Still, an explicit "keep the safety guard unchanged" note would remove all doubt.

**3. `milestone_start` placement not stated (negligible)**

Sub-step 3 requires `milestone_start` for elapsed-time calculation on the "done" early return. The plan doesn't explicitly say where to place it in the restructured function. The correct position (before `_detect_milestone_step`, matching `process_milestone` line 145) is obvious from the pattern, but it's technically unspecified.

### Positive Notes

- Single-task plan with clear sub-steps — no over-engineering or scope creep.
- Step name mapping table at the bottom removes ambiguity about how generic detector steps relate to refactor-specific phases.
- Correctly preserves refactor-mode's `PipelineStopError` on max iterations (vs implement mode's WARNING + continue), maintaining the intentional behavior difference.
- Correctly handles the `plan_review_path` threading for revision attempts (counter > 1), including the file naming pattern.
- Correctly skips `implementer.implement()` on resume from "review" step while keeping `git add -A` and `verify()` — matches the `process_milestone` pattern exactly.

PLAN_REVIEW_PASS
