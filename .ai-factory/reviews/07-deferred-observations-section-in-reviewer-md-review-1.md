## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/prompts/reviewer.md`, `docs/how-it-works.md`)
**Risk Level:** 🟡 Medium

### Context Gates
- **ARCHITECTURE.md** — present. This change is prompt+docs only; no architectural boundary impact. The `.ai-factory` CLAUDE.md note flags "review-section format" as a cross-repo contract with the skills repo (`roadmap-prune`). See Critical Issues.
- **RULES.md** — not present in this repo. No gate.
- **ROADMAP.md** — milestone line (line 25) matches the plan. Constraint "no Python changes" satisfied: `git status` shows only `docs/how-it-works.md`, `orchestrator/prompts/reviewer.md`, and plan artifacts modified — `agents.py`/`main.py` untouched. Sibling prompts untouched. `_has_signal` last-line contract preserved (new section sits above the signal in prose ordering).
- **Spec** `.ai-factory/specs/03-deferred-observations-section.md` — followed for the criterion (scope-not-severity), PASS interaction, reserved status field, and role-neutral wording. One divergence in the heading level, below.

### Critical Issues

**Heading level mismatch: prompt emits `### Deferred observations` (h3) but the standardized format is `## Deferred observations` (h2).**
`orchestrator/prompts/reviewer.md:101` places the section as a level-3 subsection of `## Code Review Summary`, siblings with `### Positive Notes`. But every authority for the standardized format specifies a level-2 heading:
- The spec (`03-deferred-observations-section.md`, "Details" bullet 1): *"add `## Deferred observations` to the review template"*.
- The roadmap line and the plan's task title: **`## Deferred observations` section**.
- The companion doc added in this very same change — `docs/how-it-works.md:51`: *"Файл ревью может содержать секцию `## Deferred observations` перед сигнальной строкой"* — states h2.

So the change is internally inconsistent: the doc it ships promises `##`, the prompt produces `###`. This is exactly the "review-section format" that CLAUDE.md marks as a contract mirrored by the skills-repo harvest consumer (`roadmap-prune` sweeping `plan-reviews/` and `reviews/`). A sweeper keyed on the documented `^## Deferred observations` heading will silently skip reviews whose section is emitted at `###` — reintroducing the exact silent-loss failure mode this milestone exists to eliminate. The fix lies entirely within this milestone's file boundary (change `###` → `##` in the template at `reviewer.md:101`, and correspondingly move it out of the `## Code Review Summary` fenced block so it reads as a top-level section, matching the spec's "after the findings sections and before the signal line"), so per the milestone's own criterion this is a finding, not a deferred observation.

### Positive Notes
- The scope-not-severity criterion, the operational test, the independent-axes clause, and the reserved-status-field / no-imitation rule (`reviewer.md:106-111`) transcribe the spec's anti-laundering guard faithfully and role-neutrally.
- REVIEW_PASS reconciliation is correct and unambiguous: the "no findings at all" rule now explicitly excepts deferred observations, and the "even one bug under any heading" rule is scoped to "any heading other than Deferred observations" (`reviewer.md:113-115`). PLAN_REVIEW_PASS parity is stated.
- Wording stays role-neutral ("milestone", "the work", "whoever should act") — the single edit correctly serves both `PlanReviewer` and the concatenated `PlannerReviewer`.
- The Russian doc sentence matches the surrounding language and describes current-state behavior without history phrasing.
