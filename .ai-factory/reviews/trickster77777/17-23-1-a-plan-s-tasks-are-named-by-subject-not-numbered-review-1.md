## Code Review Summary

**Files Reviewed:** 3 (`orchestrator/prompts/planner.md`, `orchestrator/prompts/test-planner.md`, `orchestrator/prompts/implementer.md`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture (`.ai-factory/ARCHITECTURE.md`) — PASS.** `orchestrator/prompts/` holds static system prompts, loaded whole by `_load_prompt` and never parsed; a prompt-text change crosses no layer or dependency rule.
- **Rules (`.ai-factory/RULES.md`) — WARN (file absent).** The repo carries no `RULES.md`; nothing to check against.
- **Roadmap (`.ai-factory/roadmaps/trickster77777.md:123`) — PASS.** The contract line and the plan heading match; its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/55-plan-tasks-named-not-numbered.md`, read in full, and the two handoffs the spec's §3 rationale names were opened. Phase 23's header names no `Governing spec:`.
- **Spec conformance — PASS, verified mechanically.** All four of the spec's changes landed, and both rewritten rule texts were compared character-for-character against the spec's §3 strings: the ban line at `implementer.md:108` is byte-identical modulo the `- ` list marker, and rule 7 at `:128` is byte-identical modulo the `7. ` ordinal. Both template blocks match the spec's blocks exactly, including the `<subject A>`/`<subject B>`/`<subject C>` labels, the retained `(depends on …)` wording, and the `### <group name — e.g. "TradeAggregator — core behavior">` example the test-planner header keeps.

### Verification performed

- **The spec's verify grep passes.** `grep -rnE "(Task|Phase) [0-9]" orchestrator/prompts/` returns nothing (exit 1). The five template lines and the two Step 2.3 example lines were the only digit matches and all seven are gone; `Phase N`, `Task N`/`task N.M` survive in both rule sites as illustration shapes, as the spec intends.
- **Nothing at runtime reads what changed.** The three files are data: `agents.py` concatenates them into a system prompt without parsing. `roadmap.py:93`/`:110` rewrite checkboxes on the *roadmap* line located by `task.title`, never on a plan file, so no code depends on a plan's task header shape. The diff touches no `.py` file — `git status` shows only the three prompts plus this task's own artifacts.
- **Walk order is unaffected.** `implementer.md:37` iterates "each unchecked task (`- [ ]`) in the plan, in order" — list order, never numeric — so removing the ordinals orphans no ordering contract. The `- [ ]` → `- [x]` mechanic, the `Files:` line, the two-space continuation indent, and the fences are unchanged in both templates.
- **Guards honoured.** `tests/` is untouched, so the deliberately retained `# Task N:` section comments stand as Phase 19's evidence; `reviewer.md` and `escalation.md` are untouched; no check, gate, or scan was added anywhere downstream.
- **No stale sibling text left behind.** `orchestrator/docs/` carries no plan template — `docs/reference/target-project.md:34-57`'s `- [ ] **Task A**` lines are the *roadmap* format, a different artifact, correctly not swept. Cross-repo, the `orchestrator-artifacts` engine in `skills/` documents paths, PASS signals and sidecar fields but not a plan's task-header shape, and `skills/src/skills/task-rescue/SKILL.md:123-125` explicitly tells its reader that artifact heading formats are inconsistent and must not be hardcoded — so no mirror update is owed under the root CLAUDE.md's cross-repo clause.
- **Rule 7's internal self-reference was updated with the template.** The old wording pointed at "the plan's `**Task N:**` headers"; it now reads "a plan's task headers", so the prompt no longer cites a shape the planner has stopped emitting.

### Critical Issues

None.

### Positive Notes

- **The two rule sites now lead with the principle, and the enumerations read as illustration.** Both open on the plan's standing — instruction, gone once the task closes — before naming any shape, which is what makes a construct the list never anticipated (the module docstring and the `.proto` comment that defeated the previous wording) still fall inside the rule.
- **The residual instance inside the arguing prompt was caught in the same change.** Step 2.3's example demonstrated the exact shape the task removes; leaving it would have gone stale the moment the planner stopped writing `Task 1:` headers.
- **Scope discipline is exact.** Every "nothing else changes" clause in the plan holds under diff — the surrounding prose, both rule lists' numbering, `## Task Description Requirements`, and the test-planner's grouping and test-case rules are byte-identical to HEAD.

## Deferred observations

- Affects: `.ai-factory/specs/trickster77777/55-plan-tasks-named-not-numbered.md` (Phase 23) — With the ordinal gone, a plan's task headers are unique only if their subjects are, and no prompt text states that requirement to the agent that writes them: the spec asserts "subjects within one plan are distinct" as a property, but neither replacement template nor `planner.md`'s `## Task Description Requirements` / Important Rules asks for it. Two consumers depend on it quietly — a `(depends on <subject>)` clause resolves to one task only when subjects differ, and `implementer.md:64`'s mandatory `- [ ]` → `- [x]` update needs a unique `Edit` match, so two identically-named tasks make the checkbox update fail on an ambiguous `old_string` (recoverable by widening the match to the following `Files:` line, so nothing is blocked). The exposure is sharpest in `test-planner.md:96,103`, where the two template entries are now literally identical placeholder lines (`- [ ] **<describe block subject>**` twice) that a planner may imitate, where the planner template still distinguishes `<subject A>`/`<subject B>`/`<subject C>`. Not raised as a finding because the fix means adding prose to file regions both the spec and the plan pin as untouched; it belongs to whoever owns the spec, as a distinctness clause in the planner's task requirements or the test-planner's grouping rules.

REVIEW_PASS
