## Plan Review Summary

**Plan:** 7.1 — Prompt bodies speak the language
**Files Reviewed:** 1 plan + spec `26-prompt-bodies-speak-the-language.md` + 4 target prompt files (`planner.md`, `test-planner.md`, `reviewer.md`, `implementer.md`)
**Risk Level:** 🟢 Low

### Context Gates
- **Spec tree (governing):** WARN-free. The plan is a faithful, one-to-one restatement of the spec's § "The change" tables. Every line-number citation and every guard traces back to the spec.
- **Architecture / Rules:** N/A — prose-only edits to three static prompt files read by LLM agents at session start; no module boundary, dependency rule, or code/config surface is touched.
- **Roadmap alignment:** Plan heading `# Plan: 7.1 — Prompt bodies speak the language` corresponds to the trickster77777 roadmap Phase 7 language-conformance work; spec dated 2026-07-14, amended 2026-07-18 per handoff 07 (naming-only contract). Consistent.

### Verification against ground truth
- **File paths:** Correct. Prompts live at `orchestrator/prompts/` relative to the sub-repo root (`orchestrator/orchestrator/prompts/` from the sakshi checkout). All four `.md` files exist.
- **Occurrence counts match the spec tables exactly:** `test-planner.md` 11 line-matches, `planner.md` 11, `reviewer.md` 7 (case-insensitive `\bmilestone`). `implementer.md` has **0** occurrences — confirming Task 4's `grep -rniE "\bmilestone" orchestrator/prompts/*.md → zero hits` will hold after the three files are conformed (the wildcard sweep includes `implementer.md`, which stays clean).
- **Line numbers verified:** Every line cited (planner 3/5/21/22/24/25/48/82/85/136/143; test-planner 3/5/18/19/21/22/27/29/38/76/125; reviewer 23/24/25/112/113/114/116) matches the current file contents. Multi-occurrence lines (test-planner L3 "specific milestone. The milestone…", reviewer L25 "<milestone title>…milestone's line", reviewer L112 two occurrences) are covered by the spec's New-column text.
- **Guards correctly identified and preserved:** `## Deferred observations` (reviewer L106), `- Affects:` (L108), `PLAN_REVIEW_PASS`/`REVIEW_PASS` (L118–121), and `Spec:`/`Governing spec:` tags stay byte-for-byte. Line 22/19 rename keeps the `Spec:` tag while retiring "full specification" → "full task spec". "named roadmap" and "deferred observation(s)" correctly left in ordinary-English spelling (contract binds word choice, not typography).
- **Verification tooling works in this environment:** Both Task 4 greps execute correctly here — the second (`\|` alternation) returns the protocol tokens as expected, so the confirmation step is reliable.

### Critical Issues
None.

### Positive Notes
- The plan pins each edit to an authoritative spec-table row rather than paraphrasing, eliminating implementer guesswork about *which* `task`/`Task` to leave alone versus rename.
- The plan-checklist-vs-roadmap-unit distinction (`## Tasks`, `**Task N:**`, "test tasks" stay; roadmap-unit `milestone` renames) is stated per-file and per-line, matching the spec's rationale precisely.
- Task 4 is verification-only with a clear fail→return-to-task loop, and the guard grep confirms the untouchable protocol literals rather than assuming them.
- Scope boundaries (no `.py`, docs, CLAUDE.md, ARCHITECTURE.md, config, or `implementer.md`) are explicit and consistent with the spec's Guards and "What NOT to do".

The plan is complete, accurate against the codebase and its governing spec, and safe to implement.

PLAN_REVIEW_PASS
