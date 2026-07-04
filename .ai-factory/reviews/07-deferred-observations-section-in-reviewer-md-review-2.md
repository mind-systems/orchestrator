## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/prompts/reviewer.md`, `docs/how-it-works.md`)
**Risk Level:** 🟡 Medium

_Re-review of review-1. The working tree is byte-identical to what review-1 examined — no change was made in response to the prior finding. Per-finding re-verification below._

### Re-verification of prior findings

**[review-1 · Heading level mismatch] — NOT FIXED.**
Re-read `orchestrator/prompts/reviewer.md:101` in the current tree: the template still emits `### Deferred observations` (level-3), unchanged. Cited current lines:
- `reviewer.md:101` → `### Deferred observations`
- `docs/how-it-works.md:51` → `Файл ревью может содержать секцию `## Deferred observations`` (level-2)

The internal contradiction stands verbatim: the doc shipped by this same change promises a level-2 `## Deferred observations` heading, the prompt produces level-3. `git diff HEAD` shows no edit to line 101 since review-1. Verdict: **Not fixed.**

### Context Gates
- **ARCHITECTURE.md** — present. Prompt+docs-only change; no boundary impact. CLAUDE.md marks "review-section format" as a contract mirrored by the skills-repo consumer (`roadmap-prune`); the heading level is part of that format.
- **RULES.md** — not present. No gate.
- **ROADMAP.md** — milestone line 25 matches the plan. "No Python changes" holds: `git status` shows only `docs/how-it-works.md`, `orchestrator/prompts/reviewer.md`, and plan/review artifacts. `agents.py`/`main.py` and sibling prompts untouched. Last-line signal contract preserved.
- **Spec** `.ai-factory/specs/03-deferred-observations-section.md` — followed except for the heading level (below).

### Critical Issues

**Heading level mismatch: prompt emits `### Deferred observations` (h3) but the standardized format is `## Deferred observations` (h2).**
`orchestrator/prompts/reviewer.md:101` nests the section as a level-3 subsection of `## Code Review Summary`, sibling to `### Positive Notes`. Every authority for the standardized, machine-sweepable format specifies level-2:
- Spec `03-deferred-observations-section.md`, Details bullet 1: *"add `## Deferred observations` to the review template"*.
- Roadmap line 25 and the plan's Task 1 title: **`## Deferred observations` section**.
- The companion doc added in this same change — `docs/how-it-works.md:51`: *"Файл ревью может содержать секцию `## Deferred observations`"* (h2).

The change therefore ships an internal contradiction (doc says `##`, prompt emits `###`). This is the "review-section format" that CLAUDE.md pins as a cross-repo contract with the `roadmap-prune` harvest consumer sweeping `plan-reviews/` and `reviews/`. A sweeper keyed on the documented `^## Deferred observations` heading silently skips reviews whose section arrives at `###` — reintroducing the exact silent-loss failure mode this milestone exists to eliminate. The fix is inside this milestone's file boundary (promote `reviewer.md:101` from `###` to `##`, lifting it out of the `## Code Review Summary` fenced sub-structure so it reads as a top-level section "after the findings sections and before the signal line" per the spec), so by the milestone's own scope-not-severity criterion this is a finding, not a deferred observation.

### Positive Notes
- Scope-not-severity criterion, operational test, independent-axes clause, and reserved-status-field / no-imitation rule (`reviewer.md:106-111`) transcribe the spec's anti-laundering guard faithfully and role-neutrally.
- REVIEW_PASS reconciliation is correct: the "no findings at all" rule excepts deferred observations, and the "even one bug under any heading" rule is scoped to "any heading other than Deferred observations" (`reviewer.md:113-115`), with PLAN_REVIEW_PASS parity stated.
- Wording stays role-neutral; the single edit serves both `PlanReviewer` and the concatenated `PlannerReviewer`.
- The Russian doc sentence matches surrounding language and describes current-state behavior.
