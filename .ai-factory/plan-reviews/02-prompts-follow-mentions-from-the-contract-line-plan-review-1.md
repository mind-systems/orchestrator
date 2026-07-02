# Plan Review: Prompts: follow mentions from the contract line

**Plan reviewed:** `.ai-factory/plans/02-prompts-follow-mentions-from-the-contract-line.md`
**Risk Level:** 🟢 Low

## Context Gates

- **ARCHITECTURE / RULES:** No `.ai-factory/ARCHITECTURE.md` or `RULES.md` present; no `skill-context/aif-review/SKILL.md`. No boundary or convention gates apply. (WARN — optional files absent, expected for this repo.)
- **ROADMAP linkage:** Milestone matched at `.ai-factory/ROADMAP.md:13` — **Prompts: follow mentions from the contract line**, `Spec: .ai-factory/notes/03-follow-mentions.md`. The plan's `# Plan: <title>` heading matches the roadmap line exactly, so the recovery mechanism Task 3 prescribes is itself realizable for this milestone. ✅
- **Spec fidelity:** The plan is a faithful, verbatim translation of note `03-follow-mentions.md` Edit 1 (planner + test-planner) and Edit 2 (reviewer), including the "What NOT to do" constraints (no authority language, no ordering pressure, no directory sweep, no new file/flag, implementer untouched). ✅

## Codebase Verification

Confirmed against source before finalizing:

- **All line references are accurate.**
  - `planner.md`: RULES block at lines 23-25; `---` at line 33. ✔
  - `test-planner.md`: RULES block at lines 19-20; `---` at line 22. ✔
  - `reviewer.md`: Context Gate bullets (ARCHITECTURE/RULES/ROADMAP) at lines 16-18; WARN/ERROR note at 20-22. ✔
- **The shared-prompt assumption behind Task 3 is correct.** `reviewer.md` is loaded by *both* consumers:
  - `PlanReviewer.__init__` → `_load_prompt("reviewer")` (`agents.py:322`), fresh session, receives only the plan path (`agents.py:329-337`).
  - `PlannerReviewer.__init__` → `self.reviewer_prompt = _load_prompt("reviewer")` (`agents.py:246`), used for code review in the planner's session, which already received the milestone + roadmap line literally.
  Task 3's second bullet ("*When the session holds only a plan path...*") is therefore a correctly-scoped conditional: it activates for plan review and is a graceful no-op for code review, which is exactly the behavior the note (line 11) describes. There is no separate `plan-reviewer.md`, so placing both bullets in `reviewer.md` is the only correct location. ✅
- **The `Governing spec:`/`Spec:` mentions are reachable by the planner at runtime.** The milestone description passed to the planner contains the `Spec:` tag inline, and `plan()` additionally passes `Roadmap: <path> (line N)` (`agents.py:262-263`), so the phase header is openable. The rule is actionable, not aspirational. ✅

## Non-Blocking Notes

1. **Task 1 insertion-point phrasing is slightly loose (clarity, not correctness).** The task anchors the new block to "*after the existing RULES.md bullet block (ends at line 25)*" while also saying "*before the `---` at line 33*" and "*do not alter ... the 'Use this context when' list*" (lines 27-31). The only placement satisfying all three constraints is **after the "Use this context when" list (line 31), immediately before the `---`** — not directly after line 25, which would wedge the block between the RULES bullets and the list that summarizes how to use that context. The constraints disambiguate it correctly, but an implementer skimming the first clause could misplace it. Consider stating the target as "immediately before the `---` at line 33, after the 'Use this context when' list." Note that `test-planner.md` (Task 2) has no such list, so its RULES-block-then-`---` placement is unambiguous.

2. **Register mirroring for `test-planner.md` is under-specified but low-risk.** Task 2 asks to keep the four bullets "identical in intent" while "matching `test-planner.md`'s own register." Since `test-planner.md` Step 0 has no "Use this context when" framing, the block will sit directly before `---`. This is fine and matches note Edit 1's "mirrored" instruction; flagging only so the implementer does not feel obliged to invent parallel scaffolding that doesn't exist in that file.

## Positive Notes

- Correctly scoped as prompt-only: no touch to `agents.py`, `main.py`, `roadmap.py`, or `implementer.md`, consistent with the note's constraints and the pipeline architecture.
- Additive edits only — no rewrites or removed content, minimizing regression surface on the four-agent prompt contract.
- Single-commit instruction matches the project convention (no conventional-commit prefix, descriptive imperative).
- Task 3 correctly encodes the plan-review "no root edge" problem and its `ROADMAP_TESTS.md` branch for test-plan reviews, matching `TestRunner`/test-mode reality.

The plan is accurate, well-scoped, faithful to its spec, and verified against the live codebase. The two notes above are clarity refinements, not blocking defects.

PLAN_REVIEW_PASS
