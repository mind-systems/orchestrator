## Code Review Summary

**Files Reviewed:** 3 changed source/doc files (`orchestrator/prompts/planner.md`, `orchestrator/prompts/test-planner.md`, `docs/context-model.md`)
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap alignment (PASS):** Plan `# Plan:` title matches the open milestone at `.ai-factory/ROADMAP.md:17` verbatim. Scope is prompt+docs only; the diff does not exceed the contract line.
- **Spec note (PASS):** `.ai-factory/notes/05-specs-wording.md` is the `Spec:` note. Every clause is honored — the guard half is deleted and replaced with nothing, the positive rule stays word-for-word, no generic guard is reintroduced, the `specs/`(current)/`notes/`(legacy) pair is stated once in docs, and no Python or target-project migration is touched.
- **ARCHITECTURE/RULES (N/A):** No `.ai-factory/ARCHITECTURE.md` or `RULES.md` boundary/convention conflict — this is prompt/doc text only.

### Correctness

The change set is entirely markdown prompt/doc text — there is no runtime surface, so no type mismatch, migration, or race-condition class of bug applies. Each edit was verified against the plan and spec:

- **`planner.md:25`** — the fused bullet `- Follow only links reachable from your milestone; do not sweep the notes directory or read specs of unrelated tasks.` is rewritten to `- Follow only links reachable from your milestone.` The positive depth-self-limit half is preserved; only the prohibition half is dropped. Surrounding bullets and intro line are unchanged. ✅
- **`test-planner.md:22`** — identical edit, same correct result. ✅
- **`reviewer.md`** — not in the diff, correctly left unchanged. Grep confirms its gate carries no `sweep`/`unrelated tasks` prohibition, matching the plan's "expected current state, leave unchanged" branch. ✅
- **`docs/context-model.md:20`** — the `specs/`(текущее имя)/`notes/`(легаси) pair is inserted as a phrase into the existing `Spec:`-тег bullet, preserving the Russian wording/style; no page rewrite. The clause correctly states the orchestrator is path-agnostic (agent follows the literal `Spec:` path). ✅
- **`docs/target-project.md`** — correctly left unchanged; it does not name the spec-note directory as its home, so there was nothing to update.
- **Python verification:** `grep` over `orchestrator/*.py` returns no `notes/` or `specs/` literals — no code knows either path, so behavior is unaffected. No Python files changed. ✅

### Positive Notes

- Scope discipline is exact: the prohibition half was surgically removed without disturbing the positive rule or introducing a reworded guard, matching the spec's "What NOT to do."
- The docs edit is phrase-level and language-consistent, stating the naming pair exactly once at the single point where the spec-note home is described.
- The stale roadmap assumption (that `reviewer.md`'s gate carries the guard) was correctly neutralized — no spurious edit to a file that never held the prohibition.

REVIEW_PASS
