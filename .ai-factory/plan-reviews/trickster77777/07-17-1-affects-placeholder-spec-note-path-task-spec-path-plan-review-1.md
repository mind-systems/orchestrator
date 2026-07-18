# Plan Review: 17.1 — `- Affects:` placeholder: `spec-note path` → `task-spec path`

## Code Review Summary

**Files Reviewed:** 1 plan + governing spec 29, contract line 17.1, `orchestrator/prompts/reviewer.md`, skills-side spec 73, `skills/src/skills/orchestrator-artifacts/SKILL.md`
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap — OK.** The plan's `# Plan:` heading matches contract line `.ai-factory/roadmaps/trickster77777.md:57` verbatim, under Phase 17. The line carries a resolvable `Spec:` tag → `.ai-factory/specs/trickster77777/29-affects-placeholder-task-spec-path.md`, which exists and is read. Phase 17's preamble and spec 29 agree on the lockstep framing inherited from task 7.1 / spec 26.
- **Architecture — OK (n/a).** `.ai-factory/ARCHITECTURE.md` is present; the change touches a prompt template only, crossing no module boundary and altering no agent pipeline, artifact path, or sidecar field.
- **Rules — WARN (absent).** No `.ai-factory/RULES.md` in this repo; nothing to check against. Non-blocking.
- **Governing spec chain — OK.** Spec 29 names `skills/docs/reserved-words.md` as governing; the change retires the synonym `spec-note` in favor of the registry name task spec, which is exactly what that spec mandates.

### Critical Issues

None.

### Verified against ground truth

Every factual claim in the plan was checked against the files, not against the spec's description of them:

- **Line numbers are correct.** `orchestrator/prompts/reviewer.md:106` is `## Deferred observations`; `:108` is the `- Affects:` entry line, byte-for-byte as the plan quotes it. No off-by-one.
- **Uniqueness holds.** `## Deferred observations` occurs once in the file, `- Affects: ` once. The post-edit acceptance criterion (`grep -n 'task-spec path'` → exactly one hit, line 108) is therefore satisfiable, and `task-spec path` currently appears nowhere in the repo — no pre-existing hit to confuse the check.
- **The zero-hit verify is honest about its scope.** `grep -rn 'spec-note' orchestrator/ docs/ CLAUDE.md` currently returns exactly one hit — `reviewer.md:108` — so it goes to zero on the edit. I widened the sweep repo-wide: every other surviving `spec-note` sits in `.ai-factory/` (the 17.1 contract line, spec 26's guard clause, spec 29's own "current state" quote). Those legitimately quote the pre-change state and are exempt by the plan's own stated carve-out; none is a live surface the scanner or an agent reads as instruction. The narrow grep paths are correct, not an oversight.
- **The cross-repo pin is real.** Skills spec 73 pins the target field as `<phase / task-spec path / "unknown">` — character-identical to the string spec 29 and this plan pin. Convergence genuinely comes from the shared pin, so the "either order, parallel-safe" claim holds and no ordering constraint is missing from the plan.
- **The recorded tail difference is accurate.** `SKILL.md:55` really does carry `— <observation>` while `reviewer.md:108` carries `— <one-paragraph observation>`, and both specs independently record this as a per-side difference. The plan's instruction *not* to harmonize is correct — harmonizing would be the drift, not the fix.
- **Scanned bytes are untouched by construction.** The edit falls strictly inside the placeholder, after the `- Affects: ` prefix, so neither scanned literal can move. The guard is structurally guaranteed, not merely asserted.

### Positive Notes

- The plan resists the most likely failure mode for a one-token rename: it explicitly forbids reflowing the line, the fenced block, and the criterion bullets below it, and forbids touching the sibling repo. That closes the two ways this task could quietly grow beyond its contract.
- Task 2's third check names precisely the three things that must not move (heading, prefix, PASS literals) rather than asserting the whole grep output is unchanged — which would have contradicted Task 1. The distinction between the frozen `- Affects: ` prefix and the mutable tail is stated once, in Task 1, and reused consistently.
- Scope discipline is exact: `git diff --stat` → one file, one line is a falsifiable close-out condition, not a vibe check.
- The plan correctly declines to "fix" the skills side in passing, deferring to task 17.5 by name — the right call for a jointly-owned protocol surface.

PLAN_REVIEW_PASS
