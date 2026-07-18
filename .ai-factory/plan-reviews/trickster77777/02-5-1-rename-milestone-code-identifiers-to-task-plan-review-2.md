# Plan Review: Rename `milestone` code identifiers to `task` (5.1) — round 2

**Plan:** `plans/trickster77777/02-5-1-rename-milestone-code-identifiers-to-task.md`
**Spec:** `.ai-factory/specs/trickster77777/24-code-identifiers-milestone-to-task.md`
**Roadmap:** `.ai-factory/roadmaps/trickster77777.md` → Phase 5 → 5.1
**Risk Level:** 🟡 Medium — round-1 findings are both closed, and the plan is otherwise line-accurate; but two in-scope identifiers remain unaccounted for and both would trip the plan's own Task 11 Verify grep (and one breaks at runtime).

## Round-1 status
- **Finding 1 (`main.py:178` `_git_commit` docstring)** — CLOSED. Task 4 now explicitly renames line 178 `"…after a completed milestone."` → "…completed task."
- **Finding 2 (`test_agents.py:260` comment)** — CLOSED. Task 10 now renames `# … (fixed in milestone 2.2)` → "task 2.2".

## Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): OK. A behavior-neutral symbol rename crosses no module boundary or dependency direction.
- **Rules** (`.ai-factory/RULES.md`): absent — WARN (optional file, nothing to check).
- **Roadmap alignment**: OK. Maps cleanly to Phase 5 → 5.1; the `agents.py:304` prompt-prose boundary assumption remains sound (claimed by neither Phase 6 nor Phase 7).

## Critical Issues

### 1. `main.py:384` is misfiled in Task 4's "leave byte-for-byte" group but carries the identifier `result.milestones`
Task 4's closing directive splits the mixed lines into two groups:
- *rename only the embedded identifier, keep the surrounding string* — lines **241, 311, 359, 382, 401**
- *leave strings byte-for-byte* — lines **51, 243, 362, 378, 384, 394, 402(text), 484–485, 505**

Line 384 is in the wrong group. Its actual content is:

```python
384:        print(f"Found {len(pending)} pending milestones out of {len(result.milestones)} total.")
```

This is exactly the shape of line 382 (correctly placed in the *rename-identifier* group): a `print` whose f-string contains a live `result.milestones` / `result.milestones_after_breakpoint` expression **plus** Phase-6 string words. The identifier `result.milestones` must become `result.tasks` because Task 1 renames the `ParseResult.milestones` field to `tasks`; the words "pending milestones" / "total" stay byte-for-byte.

Consequence of the misfiling, following the specific line-list literally (specific overrides the general "rename every `result.milestones` → `result.tasks`" rule stated earlier in Task 4):
- **Runtime break:** `result.milestones` on line 384 references a field that no longer exists → `AttributeError` on the non-breakpoint startup-summary path (reached whenever `breakpoint_hit` is False and work is pending).
- **Verify grep fails:** Task 11 requires every residual `[Mm]ilestone` hit to be either a Phase-6 string literal or one of the three alert-token test names. `result.milestones` at line 384 is an identifier — neither — so Task 11's grep flags it and the plan cannot satisfy its own acceptance.

Fix: move line 384 from the "leave byte-for-byte" list into the "rename only the embedded identifier" list (alongside 241, 311, 359, 382, 401). The remaining group-B lines (51, 243, 362, 378, 394, 402, 484–485, 505) are genuinely pure strings and are correctly left.

### 2. Task 7 never renames the `test_find_milestone_line_*` test-function names (`test_roadmap.py:182, 193, 202`)
The spec's rename table lists `test_find_milestone_line_*` among the test names to rename. Task 7 renames `Milestone(...)` constructions, `_find_milestone_line(...)` **calls**, `result.milestones[…]`, the `test_parse_roadmap_milestones_after_breakpoint_count` function, and an enumerated set of docstring/comment lines (1, 21, 50, 70, 90, 107, 119–120, 143, 153, 178, 183, 251, 267, 298). It does **not** cover the three test-function *definitions*:

```python
182: def test_find_milestone_line_unchecked_match():
193: def test_find_milestone_line_already_checked_returns_none():
202: def test_find_milestone_line_no_match_returns_none():
```

These are distinct symbols, not `_find_milestone_line(...)` call sites, so the plan's general "rename every `_find_milestone_line(...)`" instruction does not reach them — and under the plan's own **symbol-aware, not-blind-replace** mandate a rename of the `_find_milestone_line` function must *not* auto-touch them either. Left as-is, Task 11's grep (`grep … tests/*.py`) flags `test_roadmap.py:182,193,202` as residual identifiers outside the allowed set (they are not string literals, and not among the three protected alert-token test names), so the plan again cannot pass its own Verify.

Note the asymmetry: Task 8 handles its analogous families explicitly ("Rename all `test_detect_milestone_step_*`, `test_detect_test_milestone_step_*`, and `test_process_milestone_*` function names"). Task 7 needs the same for `test_find_milestone_line_*`. Fix: add the three function-name renames (and lines 182/193/202) to Task 7.

## Positive Notes
- Line references across the source files are otherwise exact: spot-checked `roadmap.py` (13, 30, 32, 43–70, 73–108), `resume.py` (61, 103, 169, 184), `state.py:15`, `runtime.py` (23, 39), `notify.py` (14, 15, 17), `agents.py` (70, 274, 292, 304, 306–307), and the `main.py` split (241/311/359/382/401 identifiers vs the string-only lines) — all match the code.
- The one-hard-constraint framing (identifier renamed, co-located Phase-6 string kept byte-for-byte) is applied correctly line-by-line, including the 401/402 `PipelineStopError` split.
- Round-1's two omissions are cleanly closed and each carries a precise line and target string.
- The test-fixture title strings in `test_roadmap.py` ("Done/Pending/Real milestone", "Milestone A/B", "Early/Later milestone", bare "Milestone") are correctly identified as arbitrary test data that must rename together with their assertions to stay green — not Phase-6 literals.
- The single-commit rationale holds: no sub-slice keeps the suite green (a renamed symbol without its test consumer breaks import/collection).

## Verdict
Both round-1 findings are resolved, but two new in-scope identifiers surface on close inspection: `main.py:384` (`result.milestones`, misfiled as a byte-for-byte string — breaks at runtime **and** trips the Verify grep) and the three `test_find_milestone_line_*` function names in `test_roadmap.py` (182/193/202, omitted from Task 7 — trip the Verify grep). Both fixes stay inside the milestone's file boundary, so they are findings, not deferred observations. Reclassify line 384 into Task 4's rename-identifier group and extend Task 7 to rename the `test_find_milestone_line_*` functions, and the plan is ready.
