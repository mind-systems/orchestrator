# Rename the rescue-skill references

**Date:** 2026-07-14
**Source:** conversation context — editor decomposition of Phase 8, ratified by the architect (Phase 8 split into 8.1 ready-now / 8.2 gated, along the external-dependency boundary); amended 2026-07-18 per [handoff 07](../../handoffs/07-language-contract-softened-to-naming-only.md) § 4 — the skills-side rename task moved from 11.1 / spec 64 (no longer exist) to Phase 16, task 16.1, spec 71; amended again 2026-07-18 by owner decision — the gate is lifted: docs are governing specs and lead code, so the two references name the intended skill names ahead of the skills-side rename, and skills 16.1 reconciles the code to them

## Problem today

Two docs quote the chat-skill invocation names for the milestone-rescue tooling: `docs/how-it-works.md:25` and `docs/non-convergence.md:37`, each referencing `` `/milestone-rescue` `` (and, in `non-convergence.md`, also `` `/milestone-rescue-audit` ``). The skills repo is renaming these skills to `task-rescue` / `task-rescue-audit` (its own `.ai-factory/ROADMAP.md` Phase 16, task **16.1**, spec `skills/.ai-factory/specs/71-rescue-skills-rename.md`) as part of the same reserved-words conformance effort. That rename has not landed yet (16.1 is `[ ]`; only `milestone-rescue*` dirs exist on disk) — and by owner decision the docs **lead** it: these doc lines are a governing spec, stating the intended invocation names ahead of code; skills 16.1 is the reconciliation that brings the skills repo to the names the docs now carry. Until it lands, the divergence is a known defect on the skills side, not a stale doc.

This is the one piece of Phase 8 with an external, cross-repo dependency; everything else (task 8.1, spec 27) has none and runs independently.

## The change

| File:Line | Current | New |
|---|---|---|
| `docs/how-it-works.md:25` | `` `/milestone-rescue` `` | `` `/task-rescue` `` |
| `docs/non-convergence.md:37` | `` `/milestone-rescue` `` | `` `/task-rescue` `` |
| `docs/non-convergence.md:37` | `` `/milestone-rescue-audit` `` | `` `/task-rescue-audit` `` |

This task only ever touches the skill-name substrings — the bare-word "milestone" prose sharing these lines is task 8.1's surface (spec 27) and stays untouched here, whichever of the two runs first.

## Doc-first decision — the gate is lifted

The original plan gated this task on skills 16.1 landing first ("cite the landed names, never the plan"). The owner reversed the direction on 2026-07-18: in this family the docs are governing specs and lead code, so the orchestrator's docs switch to the target names `/task-rescue` / `/task-rescue-audit` **first**, and skills 16.1 reconciles the skills repo to them. The verification duty moves to the skills side: 16.1's own guards confirm the renamed skills load and run.

## Guards

- **Frozen `.ai-factory/` history keeps the old names.** Any historical spec, handoff, or plan in this repo's own `.ai-factory/` that quotes `/milestone-rescue` or `/milestone-rescue-audit` as the record of what the skill was called at the time it was written stays untouched — this task only touches the two **live** doc references named above.
- Do not touch the roadmap-unit "milestone"→"task" prose on these two lines — that is task 8.1's surface, whether it has run yet or not.
- Do not touch any other file — this task's surface is exactly the two skill-name substrings on the two lines named above.

## Verify

- `grep -n 'milestone-rescue' docs/how-it-works.md docs/non-convergence.md` → zero hits.
- `grep -n 'task-rescue' docs/how-it-works.md docs/non-convergence.md` → both lines present.
- `git diff` touches only `docs/how-it-works.md` and `docs/non-convergence.md`.

## What NOT to do

- Do not touch frozen `.ai-factory/` history in either repo.
- Do not touch any other doc, code, or prompt file.

## Tests

None. Two-line doc reference update, static prose, loud-failure surface (a stale `/milestone-rescue` reference in a doc fails by being wrong, not by crashing anything — verified by the greps above, not a test run).
