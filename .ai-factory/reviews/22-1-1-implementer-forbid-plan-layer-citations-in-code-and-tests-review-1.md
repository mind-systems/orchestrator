# Review: 1.1 — Implementer: forbid plan-layer citations in code and tests

## Scope
`git diff HEAD` touches exactly one operative file: `orchestrator/prompts/implementer.md` (the other staged changes are the plan/plan-review/json artifacts for this milestone). Prompts-only change, as required.

## Verification against spec

- **Task 1 — DON'T bullet (line 108):** Added at the end of the `Execution Rules → DON'T` list, after the ARCHITECTURE.md conventions bullet. Forbids `Phase N`, note number, `ROADMAP`/`Plan` reference, and `.ai-factory/` path in durable code/test comments; permits self-contained explanation or a `docs/` link, naming `docs/` as the only allowed reference target. Matches the terse imperative style of the surrounding bullets. ✓
- **Task 2 — Critical Rules line (line 128):** Added as rule 7, echoing the same mandate in the file's existing echo idiom (mirrors how `NEVER write tests` appears in both lists). The trailing `All output must be in English` correctly renumbered 7 → 8, so numbering stays sequential with no collisions or gaps. ✓
- **Untouched surfaces:** The `Ground truth over the plan` block, `DEVIATION:`/`BLOCKED:` annotations, checkbox rules, NO-tests/NO-reports bullets, and pass-signal-adjacent contracts are all unchanged. No sibling prompt, Python, config, docs, or memory edits. ✓
- **Grep verification:** `.ai-factory`, `Phase N`, and `docs/` all appear on both the new DON'T bullet and the new Critical Rules line; `git diff` shows only the two additions plus the required renumber. ✓

## Correctness / runtime
No executable code changed — nothing to break at runtime (no migrations, types, or race surfaces involved). The prohibition is a positive rule fencing an emergent narration leak, which is the only mechanism that can address it (there is no instruction to delete).

## Minor observations (non-blocking)
- The implementation uses American "behavior" where the spec text wrote British "behaviour". This matches the file's existing spelling and is not a defect.

No correctness, security, or scope issues found.

REVIEW_PASS
