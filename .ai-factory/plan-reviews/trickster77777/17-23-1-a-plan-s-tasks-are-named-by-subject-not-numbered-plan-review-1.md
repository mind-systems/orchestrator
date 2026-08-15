# Plan Review — 23.1 A plan's tasks are named by subject, not numbered

**Plan:** `.ai-factory/plans/trickster77777/17-23-1-a-plan-s-tasks-are-named-by-subject-not-numbered.md`
**Files targeted:** 3 (`orchestrator/prompts/planner.md`, `test-planner.md`, `implementer.md`)
**Risk Level:** 🟢 Low

## Context Gates

- **Architecture (`.ai-factory/ARCHITECTURE.md`) — PASS.** The tree entry for `orchestrator/prompts/` reads "Static system prompts (data, not code)"; a prompt-text-only change with no code touched sits exactly inside that boundary. No layer or dependency rule is crossed.
- **Rules (`.ai-factory/RULES.md`) — WARN (optional file absent).** The repo has no `RULES.md`; nothing to check against.
- **Roadmap (`.ai-factory/roadmaps/trickster77777.md:123`) — PASS.** The contract line `23.1 — A plan's tasks are named by subject, not numbered` is present and unchecked, and the plan's `# Plan:` heading matches it. Its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/55-plan-tasks-named-not-numbered.md`, which was read in full; Phase 23's header names no `Governing spec:`, so the spec is the leaf of the doc chain, and the code leaves it names (`roadmap.py:93,110`, the prompt files) were opened directly.
- **Spec conformance — PASS, verified character-for-character.** The plan's four tasks map one-to-one onto the spec's four changes. Both verbatim rule texts (the ban line and rule 7) were diffed against the spec's §3 strings and match exactly modulo the list-marker/`7.` prefix the plan correctly adds. Both template blocks match the spec's blocks modulo the two-space list-continuation indent the plan's own nesting adds. Every guard in the spec's "Guards" and "What NOT to do" sections is carried into the plan's "Guards for every task above", including the two that most invite over-reach (no sweep of `tests/`'s existing `# Task N:` headings, no downstream check in `reviewer.md`).

## Verification performed

Line anchors and structural claims were checked against the files, not taken from the plan:

- `planner.md:94-108` — 15 lines, exactly the template body between the fence at `:93` and the closing fence at `:109`; the replacement block is also 15 lines. `planner.md` does have 8 Important Rules and a `## Task Description Requirements` heading, as the plan's "nothing else changes" clause asserts.
- `test-planner.md:94-107` — 14 lines, matching the 14-line replacement. `## Test Command`, `## Target Spec File`, `**Task grouping rules:**`, `**Test case rules:**` and `## Important Rules` all exist as named.
- `implementer.md:55-61` — the Step 2.3 fenced example; `:57`/`:60` are the only two lines carrying the label, and `**This is MANDATORY**` sits at `:63` as described. `:108` is indeed the last bullet of `### DON'T:`, and `:128` is indeed item 7 of `## Critical Rules` — both keep their position under the plan.
- **The verify grep holds.** `grep -rnE "(Task|Phase) [0-9]" orchestrator/prompts/` today returns exactly seven lines: the five template lines in `planner.md`/`test-planner.md` and the two example lines in `implementer.md`. All seven are removed by Tasks 1–4, and neither replacement rule text contains a digit after `Task`/`Phase` (`Task N`, `task N.M`, `Phase N` survive as illustration shapes only). Post-change the grep returns nothing, as the plan claims. The path prefix `orchestrator/prompts/…` resolves correctly from this repo's root (the package is nested one level: `orchestrator/orchestrator/prompts/`).
- **"No code changes" is grounded, not assumed.** `roadmap.py:93` (`mark_done`) and `:110` (`mark_skipped`) both operate on lines read from the roadmap `path` passed in, located via `_find_task_line` matching `task.title` — never on a plan file. A sweep of `orchestrator/*.py` for `**Task`, `Task [0-9]`, and `- [ ]` finds no other reader, and `agents.py:35` loads each prompt whole via `_load_prompt` without parsing it. The per-turn prompts built in `PlannerReviewer.plan`/`Implementer.implement` reference the plan only by path. Nothing in the pipeline depends on a plan's task numbering.
- **Walk order survives.** `implementer.md:37` says "For each unchecked task (`- [ ]`) in the plan, in order" — list order, never numeric order — so dropping the numbers does not orphan the ordering contract.
- **No stale sibling text is left behind.** `reviewer.md` and `escalation.md` contain no reference to a plan's task numbering; `docs/` contains no plan template and no `Task N`/`### Phase N` occurrence; the cross-repo `orchestrator-artifacts` engine in `skills/` documents the artifact protocol (paths, PASS signals, sidecar fields, deferred-observation format) but not a plan's task-header shape, so no mirror update is owed under this repo's CLAUDE.md cross-repo clause.
- **The guard about `tests/` is load-bearing and correctly stated.** Ten `# Task N:` section comments live in `tests/` today; leaving them is deliberate per the guard, and this task adds none.
- **Both handoffs the plan's Task 4 rationale leans on exist** in this repo (`.ai-factory/handoffs/08-…`, `09-…`), so the "an enumerated list has already lost twice" claim is anchored, not asserted.

## Critical Issues

None.

## Positive Notes

- **Verbatim target text removes the implementer's discretion where it matters.** Both rule rewrites and both templates are given as exact blocks rather than as instructions to paraphrase — which is the right call for a task whose entire subject is the precise wording of a rule, and the reason this review could verify conformance mechanically instead of by judgement.
- **Task 3 is correctly identified as the residual instance.** The Step 2.3 example sits inside the very prompt that argues against the shape it demonstrates; catching it in the same task, rather than leaving it to go stale the moment the planner stops emitting `Task 1:` headers, closes the loop the phase header describes.
- **The guards are written as prohibitions on plausible over-reach, not as generic boilerplate.** "No downstream check" and "no sweep of `tests/`" are exactly the two moves an implementer would be tempted into by the phase's framing, and both are named explicitly.
- **The negative claim is grounded rather than asserted.** "Nothing parses a plan's task structure" is backed by the two specific `roadmap.py` line anchors, and both check out against the code.

## Deferred observations

- Affects: `.ai-factory/specs/trickster77777/55-plan-tasks-named-not-numbered.md` (Phase 23) — The spec relies on a property that no prompt text will state after this task lands: "subjects within one plan are distinct." The number guaranteed uniqueness by construction; a subject does not, and neither the replacement template nor `planner.md`'s untouched `## Task Description Requirements` / Important Rules asserts distinctness anywhere the planner agent reads. Two consumers quietly depend on it — a `(depends on <subject>)` clause resolves to one task only if subjects are unique, and `implementer.md:64`'s "use `Edit` to change `- [ ]` to `- [x]`" needs a unique `old_string`, so two identically-named tasks make the mandatory checkbox update fail on a non-unique match. The exposure is sharpest in `test-planner.md`, whose replacement template shows two literally identical headers (`- [ ] **<describe block subject>**` twice) where the planner template distinguishes `<subject A>`/`<subject B>`/`<subject C>` — a template the planner agent may reasonably imitate. This is not raised as a finding because closing it means adding prose to a file region both the spec and the plan pin as untouched ("Nothing else in the file changes", "Everything above and below is untouched"); the fix belongs to whoever owns the spec, as a distinctness clause in `## Task Description Requirements` or in the test-planner's grouping rules. The implementer can recover in practice by widening the `Edit` match to include the following `Files:` line, so nothing here blocks this task.

PLAN_REVIEW_PASS
