## Plan Review Summary

**Plan:** Prompts/docs: drop the sweep-guard clause; specs/ naming in docs
**Files Reviewed:** plan + 6 target/reference files (`planner.md`, `test-planner.md`, `reviewer.md`, `docs/context-model.md`, `docs/target-project.md`, `orchestrator/*.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap alignment (PASS):** Plan `# Plan:` title matches `.ai-factory/ROADMAP.md:17` line verbatim. The milestone is open (`- [ ]`), scope is prompt+docs only, and the plan does not exceed the contract line.
- **Spec note (PASS):** `.ai-factory/notes/05-specs-wording.md` is the `Spec:` note behind the line. The plan faithfully implements every clause: delete the guard and replace with nothing; keep the positive rule word-for-word; state the `specs/`(current)/`notes/`(legacy) pair in docs prose; no generic guard; no Python changes; no target-project migration.
- **ARCHITECTURE/RULES (N/A):** No `.ai-factory/ARCHITECTURE.md` or `RULES.md` boundary/convention conflict — this touches prompt/doc text only.

### Correctness of Assumptions (all verified against the codebase)

- **Task 1 — `planner.md:25`:** The bullet reads exactly `- Follow only links reachable from your milestone; do not sweep the notes directory or read specs of unrelated tasks.` The quoted source and target text match the file byte-for-byte. ✅
- **Task 2 — `test-planner.md:22`:** Same bullet, identical text. Quoted strings match. ✅
- **Task 3 — `reviewer.md`:** Grep for `sweep`/`unrelated`/`do not` prohibition returns nothing. The gate bullet (`reviewer.md:19`) ends with "findings are judged against this tree, not against the roadmap line alone" and carries **no** sweep/depth prohibition. The plan correctly treats this as a verify-only, leave-unchanged task — this is the "expected current state" branch. ✅
  - Note: the ROADMAP contract line asserts the guard also lives in "reviewer.md's gate," but it factually does not (the prior "follow mentions" milestone never added a prohibition to the reviewer). The plan defuses this stale assumption cleanly with its conditional ("if none is present … leave the file unchanged") — good defensive framing rather than a blind edit.
- **Task 4 — docs:** `docs/context-model.md:20` matches the quoted bullet exactly and is the correct insertion point. Grep of `docs/target-project.md` finds no naming of the spec-note directory as its home → the plan's "leave unchanged unless a naming is present" instruction is correct. The other `docs/` matches (`non-convergence.md:15,29`, `phase-sessions.md:47`) use "нот(ы)" only conceptually and do **not** name the directory as the specs' home, so the plan's decision to scope edits to `context-model.md` is right and misses nothing. ✅
- **Python verification:** `grep -rn "notes/\|specs/" orchestrator/*.py` returns no matches — no Python literal knows either path. The plan's "verification only, no Python changes" stance is accurate. ✅

### Minor Notes (non-blocking, WARN)

- **WARN — Task 3 parenthetical wording:** The plan's aside says keep "findings are judged against the tree lifted from the milestone's line," but the actual `reviewer.md:19` wording is "findings are judged against this tree, not against the roadmap line alone." Since Task 3 leaves the file unchanged, this discrepancy triggers no wrong action — but the implementer should not attempt to "reconcile" the wording. The instruction to leave the file untouched governs.
- **WARN — Task 4 mixes an edit with two verifications** (docs edit + `target-project.md` check + Python grep). This is fine for a small prompt/docs milestone, but the implementer should treat the `target-project.md` and Python parts as pure grep-confirmations with an expected null result, not as edits.

### Positive Notes

- Every quoted source string was checked against the live files and matches exactly — the plan will not fail on a stale/mismatched `old_string`.
- Scope discipline is excellent: explicit "replace with nothing / no generic guard" guidance prevents the classic re-introduction of a reworded prohibition, matching the spec note's "What NOT to do."
- The plan correctly anticipates and neutralizes the one stale assumption embedded in the roadmap contract line (reviewer.md guard) rather than propagating it into a spurious edit.
- Correctly preserves the existing Russian wording/style in docs and inserts the `specs/`//`notes/` pair as a phrase, not a rewrite.

PLAN_REVIEW_PASS
