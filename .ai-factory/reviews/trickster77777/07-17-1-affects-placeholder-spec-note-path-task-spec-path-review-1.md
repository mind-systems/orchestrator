## Code Review Summary

**Files Reviewed:** 1 code file (`orchestrator/prompts/reviewer.md`, read in full) + plan, spec 29, contract line 17.1, skills-side spec 73 and `skills/src/skills/orchestrator-artifacts/SKILL.md`
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK (n/a).** `.ai-factory/ARCHITECTURE.md` is present. The change edits a placeholder inside a prompt template; it crosses no module boundary and alters no agent pipeline, artifact path, or sidecar field.
- **Rules — WARN (absent).** No `.ai-factory/RULES.md` in this repo. Nothing to check against; non-blocking.
- **Roadmap — OK.** The plan's `# Plan:` heading matches contract line `.ai-factory/roadmaps/trickster77777.md:57` verbatim under Phase 17. The `Spec:` tag resolves to `.ai-factory/specs/trickster77777/29-affects-placeholder-task-spec-path.md`, which exists and was read. Phase 17's preamble, spec 29, and the plan agree.
- **Governing spec chain — OK.** Spec 29 names `skills/docs/reserved-words.md` as governing; the change retires the synonym `spec-note` in favor of the registry name task spec — exactly what the phase mandates.

### Critical Issues

None.

### Verified against ground truth

The diff was checked at byte level, not read as prose:

- **Exactly one byte-run changed.** `od -c` of line 108 pre- and post-change is identical except `s p e c - n o t e` → `t a s k - s p e c`. The `- Affects: ` prefix (through its trailing space), the em dash, and the tail `<one-paragraph observation>` are byte-for-byte unchanged. The scanned literals could not have moved — the edit falls strictly inside the placeholder.
- **`## Deferred observations` (line 106) untouched.** Confirmed unchanged in the diff and still the sole occurrence in the file.
- **PASS literals untouched.** `REVIEW_PASS` / `PLAN_REVIEW_PASS` occur only at lines 118–121 and 135, all outside the diff hunk.
- **The cross-repo pin matches character-for-character.** Skills spec 73:20 pins `- Affects: <phase / task-spec path / "unknown"> — <observation>`; the field string `<phase / task-spec path / "unknown">` is identical to what landed here. Convergence comes from the shared pin, as both specs claim.
- **Parallel-safety holds in practice.** `SKILL.md:55` still carries `spec-note path` — skills 17.5 has not run. Since neither side touches the scanned bytes and the scanner keys on the heading and the `- Affects: ` prefix only, the pair is correct in this intermediate state; no ordering constraint was violated.
- **The recorded tail difference was correctly preserved.** `SKILL.md:55` carries `— <observation>`, `reviewer.md:108` carries `— <one-paragraph observation>`. The implementer did not "harmonize" them — the right call; harmonizing would have been the drift.
- **No runtime surface parses these bytes.** `grep` over `orchestrator/*.py` and `tests/*.py` for `Affects` / `Deferred observations` returns nothing, so there is no parser, fixture, or assertion to break. No test updates were needed and none were made — consistent with the plan's `Testing: no`.

### Verification checks re-run independently

- `grep -n 'task-spec path' orchestrator/prompts/reviewer.md` → one hit, line 108. ✅
- `grep -rn 'spec-note' orchestrator/ docs/ CLAUDE.md` → zero hits (exit 1). ✅
- `grep -n '## Deferred observations\|- Affects:\|PLAN_REVIEW_PASS\|REVIEW_PASS' …` → heading, prefix, and PASS literals unchanged. ✅
- `git diff HEAD --stat -- orchestrator/` → 1 file, 1 insertion, 1 deletion. ✅

### Positive Notes

- Scope discipline is exact. The change is one token; nothing was reflowed, no adjacent bullet was "improved in passing", and the sibling skills repo was correctly left to task 17.5.
- The implementer resisted the two failure modes the plan named explicitly — harmonizing the tails across repos, and touching the scanned prefix — and did neither.
- The surviving `spec-note` occurrences elsewhere in the repo all sit in `.ai-factory/` and legitimately quote the pre-change state (the contract line, spec 26's guard clause, spec 29's own "Current state" block). None is a live instruction surface; leaving them is correct, not an omission.

REVIEW_PASS
