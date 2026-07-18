# Plan: 17.1 — `- Affects:` placeholder: `spec-note path` → `task-spec path`

## Context
The reviewer prompt's deferred-observations entry template carries the retired synonym `spec-note` for the reserved word task spec. This is the sanctioned lockstep change Task 7.1 deferred: one field on one line in `orchestrator/prompts/reviewer.md`, pinned identically by the parallel skills-side task 17.5.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Conform the placeholder field

- [x] **Task 1: Rename the `- Affects:` placeholder field to `task-spec path`**
  Files: `orchestrator/prompts/reviewer.md`
  Line 108 currently reads:
  ```
  - Affects: <phase / spec-note path / "unknown"> — <one-paragraph observation>
  ```
  Change the single field `spec-note path` → `task-spec path`, so the line becomes exactly:
  ```
  - Affects: <phase / task-spec path / "unknown"> — <one-paragraph observation>
  ```
  This is a one-token edit — do not reflow, re-wrap, or otherwise reformat the line, the surrounding fenced block, or the `**Deferred observations criterion:**` bullets below it (lines 111–116).

  Hard guards (cross-repo contract with the skills-side scanner, per spec `29-affects-placeholder-task-spec-path.md`):
  - The `## Deferred observations` heading (line 106) stays byte-identical — it is a scanned literal.
  - The `- Affects: ` prefix (through the trailing space) stays byte-identical — also scanned.
  - The tail `— <one-paragraph observation>` stays as-is. The skills side keeps its own `— <observation>` wording; per the spec this is a recorded per-side difference (length instruction vs. format description), not drift — do not "harmonize" it.
  - `PLAN_REVIEW_PASS` / `REVIEW_PASS` literals and the `Spec:` / `Governing spec:` tags anywhere in the file are untouched.
  - Touch no file other than `orchestrator/prompts/reviewer.md`. In particular, do not edit the skills repo — task 17.5 owns that side and runs independently, in either order.

- [x] **Task 2: Verify the conformance** (depends on Task 1)
  Files: none (verification only)
  Run from the repo root (`/Users/max/projects/sakshi/orchestrator`):
  - `grep -n 'task-spec path' orchestrator/prompts/reviewer.md` → exactly one hit, line 108.
  - `grep -rn 'spec-note' orchestrator/ docs/ CLAUDE.md` → zero hits (frozen `.ai-factory/` history is exempt and is not covered by these paths).
  - `grep -n '## Deferred observations\|- Affects:\|PLAN_REVIEW_PASS\|REVIEW_PASS' orchestrator/prompts/reviewer.md` → heading, prefix, and PASS literals unchanged from before the edit.
  - `git diff --stat` → one file, one line changed.
