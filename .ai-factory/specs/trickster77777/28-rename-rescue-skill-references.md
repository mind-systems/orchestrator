# Rename the rescue-skill references (gated)

**Date:** 2026-07-14
**Source:** conversation context — editor decomposition of Phase 8, ratified by the architect (Phase 8 split into 8.1 ready-now / 8.2 gated, along the external-dependency boundary)

## Problem today

Two docs quote the chat-skill invocation names for the milestone-rescue tooling: `docs/how-it-works.md:25` and `docs/non-convergence.md:37`, each referencing `` `/milestone-rescue` `` (and, in `non-convergence.md`, also `` `/milestone-rescue-audit` ``). The skills repo is renaming these skills to `task-rescue` / `task-rescue-audit` (its own `.ai-factory/ROADMAP.md` task **11.1**, spec 64) as part of the same reserved-words conformance effort — but that rename has **not landed yet** as of this writing (11.1 is still `[ ]`). This task updates the orchestrator's two references to the skills' **landed** names, once they exist — never to the plan for them.

This is the one piece of Phase 8 with an external, cross-repo dependency; everything else (task 8.1, spec 27) has none and runs independently.

## The change

| File:Line | Current | New |
|---|---|---|
| `docs/how-it-works.md:25` | `` `/milestone-rescue` `` | `` `/task-rescue` `` |
| `docs/non-convergence.md:37` | `` `/milestone-rescue` `` | `` `/task-rescue` `` |
| `docs/non-convergence.md:37` | `` `/milestone-rescue-audit` `` | `` `/task-rescue-audit` `` |

Both edits are on the same two lines task 8.1 (spec 27) already conformed for the roadmap-unit word "milestone" elsewhere on those lines — this task only ever touches the skill-name substring, never re-touches the prose word "task" that 8.1 already placed there.

## Gate — pin it hard, verify before touching anything

This task is **not ready** until, in the **skills repo**:

1. `skills/.ai-factory/ROADMAP.md` task **11.1** ("The 'roadmap cleanup' coupling: conform to reserved-words + rename the rescue skills", spec 64) is marked `[x]`.
2. The renamed skill directories actually exist on disk — `src/skills/task-rescue/` and `src/skills/task-rescue-audit/` (or wherever the skills repo's landed layout places them; confirm the actual path from the skills repo at the time this task runs, not from this spec's memory of it).

If either check fails, **stop — do not edit these files.** Report back that the gate is still closed; this task stays `[ ]` until it reopens. Cite the landed names only when both checks pass — never the plan for them, and never a guess at what the final name will be.

## Guards

- **Frozen `.ai-factory/` history keeps the old names.** Any historical spec, handoff, or plan in this repo's own `.ai-factory/` that quotes `/milestone-rescue` or `/milestone-rescue-audit` as the record of what the skill was called at the time it was written stays untouched — this task only touches the two **live** doc references named above.
- Do not touch the roadmap-unit "milestone"→"task" prose on these two lines — that is task 8.1's surface, already done by the time this task runs.
- Do not touch any other file — this task's surface is exactly the two skill-name substrings on the two lines named above.

## Verify

- `grep -n 'milestone-rescue' docs/how-it-works.md docs/non-convergence.md` → zero hits.
- `grep -n 'task-rescue' docs/how-it-works.md docs/non-convergence.md` → both lines present.
- `git diff` touches only `docs/how-it-works.md` and `docs/non-convergence.md`.

## What NOT to do

- Do not run this task before confirming the gate (skills' 11.1 `[x]` and the renamed skill dirs present).
- Do not touch frozen `.ai-factory/` history in either repo.
- Do not touch any other doc, code, or prompt file.

## Tests

None. Two-line doc reference update, static prose, loud-failure surface (a stale `/milestone-rescue` reference in a doc fails by being wrong, not by crashing anything — verified by the greps above, not a test run).
