# Handoff — durable code cites the fluid plan layer: the orchestrator's side of the fix

## 1. Frame
The skills-family session diagnosed a class-level corruption — implementers stamp plan labels (`// Phase 9.3.1`, `// note 39`) into durable code/tests, and `roadmap-prune`'s number reuse later turns those citations into *false* resolutions — and settled a coordinated fix whose **source-side half lives in this repo**; this handoff carries that half. The originating session's context isn't available here — trust these files, not memory.

## 2. Read-first map

### Must-read now (minimal rehydration set)
- `~/projects/skills/.ai-factory/handoffs/15-code-cites-fluid-plan-layer-false-resolution.md` — **the full class analysis** (skills side): the failure table, the three-skill emergence, the principle, the remediation candidates. Read this first; everything below is its orchestrator-facing distillation.
- `~/projects/skills/src/skills/roadmap-engine/SKILL.md` (~:107–118) — the number-reuse mechanism half 1: phase numbers are globally sequential across the file, "gaps are legal and expected (pruning leaves holes)". This is *correct* and will not change.
- `~/projects/skills/src/skills/roadmap-prune/SKILL.md` (Step 4, ~:196–263) — half 2: completed `[x]` phases move to `ARCHITECTURE.md ## Features` at feature→one-hash grain and the roadmap lines are deleted; the freed number is reused by a later direction. Note the grain — `## Features` has **no** sub-phase resolution, so `Phase 8.1.2` has no correct target anywhere once its phase is pruned.

### Read on demand
- `~/projects/skills/src/skills/aif/references/rules-generation.md` — why the rule does **not** go into the generated `rules/base.md` body: that file is per-project counter-defaults from code evidence, "the costliest instruction surface per line"; a family-universal rule would abuse it. base.md gets only a fixed pointer line.
- `~/projects/skills/src/global/CLAUDE.md` § "Documentation style" — the skills-side authoritative home of the rule (sibling of "Describe behaviour, not code" and "One home per fact"). Whether this file reaches *this repo's* implementer is the open question in §4.
- `tradeoxy_core/.ai-factory/specs/49-purge-roadmap-refs-from-code.md` (cited by number — that repo, not this one) — the **instance** fix already in flight (task 34.6, a pure code-comment sweep). For awareness only; the class fix is this handoff.

## 3. Current state

**Done:**
- Diagnosis grounded against the real skill files (not prose): the mechanism in `roadmap-engine`/`roadmap-prune` is exactly as described; `## Features` cannot rescue sub-phase citations.
- Ownership decomposed with the user (see §7): **cause** = the orchestrator/editor writing the plan label into code (this repo); **amplifier** = skills-side number reuse (correct, frozen); **seam** = durable→fluid citation, owned by nobody.
- Verified the leak does **not** originate in the skills-side planning specs: `grep` over `roadmap-decompose*` found no annotation instruction. So fixing a decompose spec would miss the source — the source is the implementer.
- Skills-side plan settled: authoritative rule in `src/global/CLAUDE.md`; a fixed *pointer* line (not a generated rule) in the `base.md` template; a warn-only citation scan added to `roadmap-prune` at the arming moment.

**In-flight:**
- Nothing edited in either repo this session (planning/discussion only). The skills-side edits are queued, not written.

**Uncommitted working-tree state:**
- none (in this repo). In the skills repo, source handoff `15-…md` is untracked.

## 4. Next step
Two things, both in this repo, both discussion-first (the user said «поговю с ним тоже» — will talk to this agent before any edit; do **not** edit prompts unprompted):

1. **Answer the load-bearing question:** do the orchestrator and its paired-editor run under `~/.claude/CLAUDE.md`? If **yes**, the skills-side global rule already reaches the implementer and this repo needs only to stay aligned. If **no** (this repo runs its own runtime/prompt), the global never reaches the writer and the *load-bearing* home of the prohibition must be **this repo's own implementer/editor prompt** — locate where that prompt lives (start from `orchestrator/main.py` and the prompt strings it threads; the paired-editor prompt likewise) and plan the insertion.
2. **Plan a positive prohibition** wherever the prompt lands — because the leak is *emergent* (it happens with no "annotate" instruction, just from the implementer narrating its current task), deleting an instruction is insufficient; the prompt must positively forbid it: *generated code and test comments cite behaviour or a `docs/` file that owns it — never a phase number, note number, ROADMAP/Plan reference, or `.ai-factory/` path.* Provenance is answered by `git blame` → commit → `ARCHITECTURE.md ## Features`, not by a string frozen into a comment.

## 5. Working discipline
- Plan in chat; the orchestrator implements — never edit `orchestrator/*.py` or prompt files in the planning session. Present options with one recommendation; confirm before structural decisions.
- Never commit without explicit permission.
- Artifacts in English regardless of conversation language; the user converses in Russian and wants flowing prose, not compressed bullets.

## 6. Error log
- Early in the session the orchestrator was framed as a possibly-opaque external runtime, which made the fix look unreachable. Correction: `~/projects/orchestrator` is a repo the user owns (handoffs 01–04 present) — so the root-prevention fix (its own prompt) is landable here, not just a flag-to-upstream. Lesson: confirm the artifact exists before reasoning about its reachability.

## 7. Orientation
- **Cause vs amplifier vs seam** — keep these distinct. The number reuse in `roadmap-prune` looks like the bug but is a deliberate self-healing property of the fluid plan layer and must not be "fixed". The bug is the *citation crossing the `.ai-factory/` boundary*, and its writer is the implementer in this repo.
- **The boundary is directional, not a blanket ban on phase numbers.** The plan layer citing *itself* (a spec referencing `spec 44`, a contract line's `Spec:` tag) is fine — those live and die together inside `.ai-factory/`. The rule is precisely: *nothing outside `.ai-factory/` may cite into it.*
- **Dangling vs false.** A pruned-and-not-reused number gives a dead link (honestly stops a reader); a pruned-and-*reused* number gives a false resolution (confidently points at the wrong live phase). The second is the real hazard, and it is strictly worse — that is why "still resolves today" is luck, not safety.

## 8. Domain model spine
- **The principle (don't re-litigate):** durable artifacts (code, tests, docs) never reference the fluid plan layer. A comment either explains behaviour/why self-contained, or links to a durable `docs/` file that owns that behaviour. Home of the rule on the skills side: `~/projects/skills/src/global/CLAUDE.md` § "Documentation style".
- **Provenance has a home, and it isn't a comment string:** git history + `ARCHITECTURE.md ## Features` (commit-anchored, reachable via `temporal-tree`). "Which task built this" = `git blame` → the commit → the Features row.

## 9. Hard rules
- Never commit without explicit permission.
- Prompt/behaviour changes are structural — plan and confirm before touching any prompt.
- English in all written artifacts.

## 10. Cross-cutting contracts / invariants checklist
- The citation shapes to forbid in generated code/tests (the same set the skills-side prune warn-scan will grep for): `Phase N` / `Phase N.M`, `note NN`, `ROADMAP` / `Plan N` references, and any `.ai-factory/(specs|notes)` path.
- The rule is single-homed on the skills side (`src/global/CLAUDE.md`); anything this repo writes to enforce it (a prompt line) is a **pointer to that home**, never a restated copy — one fact, one home.
- Alignment target if #4 lands a prompt rule: it must match the skills-side wording exactly enough that the two surfaces never drift into contradicting each other about what "cite behaviour, not the plan" means.
