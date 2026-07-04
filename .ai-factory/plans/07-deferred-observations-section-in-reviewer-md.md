# Plan: `## Deferred observations` section in `reviewer.md`

## Context
Give reviewers a standardized, machine-sweepable home for verified-but-out-of-scope observations so they survive a passing review and can be harvested by downstream tooling, without turning them into blocking findings.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes (single Russian doc touch)

## Tasks

### Phase 1: Reviewer prompt

- [x] **Task 1: Add `## Deferred observations` to the Output Format template**
  Files: `orchestrator/prompts/reviewer.md`
  In the `## Output Format` section, insert a `## Deferred observations` block into the fenced review template — positioned **after** the findings sections (after `### Positive Notes`) and **before** the `REVIEW_PASS` rules / signal line, so the section always precedes the signal. Entry shape exactly: `- Affects: <phase / spec-note path / "unknown"> — <one-paragraph observation>`. State the reviewer rule inline: everything verified but consciously not blocked goes here, each with an addressee; if nothing was deferred, omit the section entirely. Keep wording **role-neutral** — no "code" / "plan" phrasing, since this one file is the whole `PlanReviewer` prompt and the tail of the concatenated `PlannerReviewer` prompt, so both `plan-reviews/` and `reviews/` inherit it. Mirror the existing template style (matching the `## Code Review Summary` fenced block).

- [x] **Task 2: Add the scope-not-severity deferral criterion (anti-laundering guard)** (depends on Task 1)
  Files: `orchestrator/prompts/reviewer.md`
  Alongside the new section, state the deferral criterion explicitly: an observation may be deferred **only if its fix lies outside the current milestone's scope** — a different phase, a not-yet-existing future consumer, or a file boundary the plan does not touch. Anything introduced by the current diff or fixable within the milestone's boundary is a **finding regardless of severity — down to cosmetics** (e.g. a stale comment in a changed file is a finding). Include the operational test verbatim in spirit: "if the implementer could fix this on the next iteration without leaving the milestone's file boundary or contradicting the plan — it is a finding." Make clear the two axes (scope vs. severity) are independent: "it's only LOW" is never grounds for deferral.

- [x] **Task 3: Extend the PASS rules so deferred observations are not findings** (depends on Task 1)
  Files: `orchestrator/prompts/reviewer.md`
  Amend the `**REVIEW_PASS rules:**` block with an explicit clause: deferred observations are **not findings** — a review whose only content is deferred observations still ends with `REVIEW_PASS` (and the same applies to `PLAN_REVIEW_PASS` in plan review). Ensure the existing "no findings at all → REVIEW_PASS" wording is reconciled so it cannot be read as "the Deferred observations section counts as a finding". Do not change the signal placement (still last line) or the `## Final Output Rule` (reviewer still outputs only `done`).

- [x] **Task 4: Reserve the status field for downstream tooling** (depends on Task 1)
  Files: `orchestrator/prompts/reviewer.md`
  Add a rule stating the reviewer never writes, copies, or updates any status/processing marker on deferred-observation entries — anything after the observation text is reserved for downstream consumers (skills-repo harvest/audit tools, e.g. `promoted → <spec>`). Explicitly instruct: when re-reviewing a milestone whose earlier review files already carry such marks, do not imitate them; a fresh review always emits unmarked entries. Do not add or describe the harvest step here — it lives in the skills repo (`roadmap-prune`).

### Phase 2: Docs

- [x] **Task 5: Document the section in the file-protocol description** (depends on Task 1)
  Files: `docs/how-it-works.md`
  In the "Файловый протокол" / "Сигналы завершения" area (around lines 43–49), add a current-state sentence noting that review files may carry a `## Deferred observations` section before the signal line — a non-blocking channel for out-of-scope observations that does not affect PASS/FAIL. Write in **Russian** to match the surrounding doc. Describe behavior only, no history phrasing.

## Notes for the implementer
- No Python changes. `agents.py` / `main.py` must remain untouched — `_has_signal` checks only the last line, and the new section sits above it. Verify by grep that these files are not modified.
- Do not touch sibling prompts (`planner.md`, `test-planner.md`, `implementer.md`).
- All prompt wording must stay role-neutral so a single edit serves both reviewer roles.
