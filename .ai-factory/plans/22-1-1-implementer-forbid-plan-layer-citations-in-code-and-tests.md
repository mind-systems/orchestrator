# Plan: 1.1 — Implementer: forbid plan-layer citations in code and tests

## Context
Fence an emergent leak where the implementer stamps its current-task label (`// Phase 9.3.1`, `// note 39`, an `.ai-factory/specs/…` path) into durable code/test comments — citations that `roadmap-prune`'s number reuse later resolves to the wrong live phase. Add a short positive prohibition to `prompts/implementer.md` only.

## Settings
- Testing: no
- Logging: none
- Docs: no

## Tasks

### Phase 1: Add the prohibition

- [x] **Task 1: Add the DON'T bullet**
  Files: `orchestrator/prompts/implementer.md`
  In the **Execution Rules → DON'T** list (currently ends at line 107 with the `.ai-factory/ARCHITECTURE.md` conventions bullet), append one new bullet forbidding plan-layer citations in durable code/test comments. Wording per the spec: a code or test comment never carries a `Phase N`, a note number, a `ROADMAP`/`Plan` reference, or any `.ai-factory/` path; it either explains the behaviour self-contained or links a file under `docs/` that owns it — `docs/` is the only reference target allowed in code. Match the terse imperative style of the surrounding DON'T bullets. Do not touch the `Ground truth over the plan` block, the `DEVIATION:`/`BLOCKED:` annotations, the checkbox rules, or the NO-tests/NO-reports bullets.

- [x] **Task 2: Add the Critical Rules line** (depends on Task 1)
  Files: `orchestrator/prompts/implementer.md`
  In the **Critical Rules** numbered list (lines 121–127), insert one new numbered line echoing the same rule as a hard mandate — following the file's existing echo idiom where `NEVER write tests` appears both in DON'T and Critical Rules. Renumber the trailing `All output must be in English` line accordingly so numbering stays sequential. Keep it short and operational; do not restate the skills-side rationale. Leave every other Critical Rules line (checkbox, ground-truth/DEVIATION, one-task-at-a-time, build-fix, pass-signal-adjacent contracts) unchanged.

### Guardrails (apply to both tasks)
- **Prompts only** — no Python, no config, no docs, no memory (`~/.claude/CLAUDE.md` stays as-is).
- **Sibling prompts untouched** — no edit to `planner.md` / `test-planner.md` / `reviewer.md`; plans live inside `.ai-factory/` and cite the plan layer legally.
- **Directional boundary** — the rule forbids durable code/tests citing *into* `.ai-factory/`; plan-layer-internal references (the `DEVIATION:`/`BLOCKED:` plan-file annotations, `Spec:`-tag/plan reads, checkbox updates) stay legal and untouched.
- **Verification** (per spec): `grep -ni "\.ai-factory\|Phase N\|docs/" orchestrator/prompts/implementer.md` shows the DON'T bullet and the Critical Rules line both present; `git diff` shows only the two additions (plus the renumber) and no other block changed.
