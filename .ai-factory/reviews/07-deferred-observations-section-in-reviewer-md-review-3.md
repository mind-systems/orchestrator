## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/prompts/reviewer.md`, `docs/how-it-works.md`)
**Risk Level:** 🟡 Medium

_Re-review of review-1/review-2. `git diff HEAD` is byte-identical to both prior rounds — no edit was made in response to either. Per-finding re-verification below._

### Re-verification of prior findings

**[review-1 / review-2 · Heading level mismatch] — NOT FIXED.**
Re-read the current tree:
- `orchestrator/prompts/reviewer.md:101` → `### Deferred observations` (level-3).
- `docs/how-it-works.md:51` → `Файл ревью может содержать секцию `## Deferred observations`` (level-2).

Unchanged from review-1. `git diff HEAD` shows no modification to line 101. Verdict: **Not fixed.**

### Context Gates
- **ARCHITECTURE.md** — present. Prompt+docs-only change; no boundary impact. CLAUDE.md pins "review-section format" as a contract mirrored by the skills-repo consumer (`roadmap-prune`).
- **RULES.md** — not present. No gate.
- **ROADMAP.md** — milestone line 25 matches the plan. "No Python changes" holds: `git status` shows only `docs/how-it-works.md`, `orchestrator/prompts/reviewer.md`, and plan/review artifacts. `agents.py`/`main.py` and sibling prompts untouched; last-line signal contract intact.
- **Spec** `03-deferred-observations-section.md` — followed except for the heading level.

### Critical Issues

**Heading level mismatch: prompt emits `### Deferred observations` (h3); the standardized format is `## Deferred observations` (h2).**
This does not depend on any assumption about the external harvester. The defect is a hard internal contradiction shipped **within this same diff**: `docs/how-it-works.md:51` documents the review artifact as carrying a section `## Deferred observations` (h2), while `orchestrator/prompts/reviewer.md:101` instructs the reviewer to emit `### Deferred observations` (h3). Two files in one changeset disagree on the format of the same artifact — one of them is wrong. Both the spec (Details bullet 1: *"add `## Deferred observations` to the review template"*) and the roadmap/plan Task 1 title (**`## Deferred observations` section**) resolve the ambiguity toward h2.

The milestone's stated deliverable is a *standardized, machine-sweepable* section. Shipping it at a heading level that contradicts its own companion documentation defeats that purpose, and is fixable entirely within this milestone's file boundary — so by the milestone's own scope-not-severity criterion it is a finding, not a deferred observation.

**Fix (single edit):** at `orchestrator/prompts/reviewer.md:101`, change `### Deferred observations` to `## Deferred observations`, promoting it out of the `## Code Review Summary` h3 sub-structure to a top-level section that still sits after the findings sections and before the signal line — matching the doc and the spec.

### Positive Notes
- Scope-not-severity criterion, operational test, independent-axes clause, and reserved-status-field / no-imitation rule (`reviewer.md:106-111`) faithfully and role-neutrally transcribe the spec's anti-laundering guard.
- REVIEW_PASS reconciliation is correct: deferred observations are excepted from the "no findings at all" rule and from the "any heading" clause (`reviewer.md:113-115`), with PLAN_REVIEW_PASS parity stated.
- Wording is role-neutral; the single edit serves both `PlanReviewer` and the concatenated `PlannerReviewer`.
- The Russian doc sentence matches surrounding language and describes current-state behavior.
