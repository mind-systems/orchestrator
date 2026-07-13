# Handoff — the skills family now has a reserved-words language; conform the orchestrator + the rescue skills are renamed

> Cross-repo handoff from the skills side. The skills repo has formalized a **language** — a fixed reserved-words contract — and is bringing its whole codebase into conformance (skills direction "Language integration", phases 9–13). Two things reach the orchestrator: (1) the language convention itself, which the orchestrator both *speaks* and *stores*, and (2) a skill rename it must follow. This is the orchestrator-side counterpart of skills task 11.1.

## 1. The language convention exists now

The skills family is written in a fixed vocabulary, specified as a contract:
- **`skills/docs/reserved-words.md`** — the semantics: the reserved words, their single canonical forms (multi-word terms are **kebab-case**, like Claude's own `allowed-tools`), and the one-word-one-meaning rule. It binds everything the system *produces* (docs, specs, roadmaps, skill bodies) — not the user's input, which the agent maps by context.
- **`skills/docs/skill-description-field.md`** — how it loads (the always-loaded `description:` layer as part of the system prompt).
- The **root `CLAUDE.md`** now has a `## The language` section that mandates reading `skills/docs/reserved-words.md` — it governs **both** sub-repos, skills and orchestrator alike.

The orchestrator is a first-class speaker of this language: `sidecar`, `PASS-signal`, `deferred-observations`, `task`, `phase`, `task-spec`, `governing-spec`, `contract-line` are all reserved words the orchestrator's prompts, code, docs, and artifacts use. Its own surfaces should conform — the exact same class of change the skills repo is doing to `src/`.

## 2. The reserved-word forms to fix on the orchestrator side

Read `reserved-words.md` for the full set; the ones the orchestrator most likely still spells the old way:
- `milestone` (the processed roadmap unit) → **`task`** (the orchestrator marks `[x]` at the task tier). `phase` is the strategic tier above it.
- `spec note` → **`task-spec`**; `contract line` → **`contract-line`**; `governing spec` → **`governing-spec`**.
- `PASS signal` → **`PASS-signal`**; `deferred observations` → **`deferred-observations`**.
- Multi-word terms hyphenate: `named roadmap` → `named-roadmap`, `owner line` → `owner-line`, etc.

**Tags are legacy — do not rename them.** The on-disk `` Spec: `` tag on a contract-line, the `Governing spec:` tag on a phase header, and the `.ai-factory/specs/` directory stay exactly (tag ≠ reserved word). Only prose/vocabulary conforms.

## 3. The rescue skills are renamed

`milestone` is retired even from skill names. The skills repo renames:
- **`milestone-rescue` → `task-rescue`**
- **`milestone-rescue-audit` → `task-rescue-audit`**

The orchestrator **invokes these skills by name** and references them in its docs. Known references (grep hit): `orchestrator/docs/how-it-works.md`, `orchestrator/docs/non-convergence.md` — and check wherever the orchestrator names a skill to invoke (prompts, config, `orchestrator.json`, code, tests). Update every live reference to the new names. Frozen history (past handoffs, plans, reviews, completed specs) keeps the old names as the record of what the skill was called then — the skills side leaves its history untouched; do the same here.

The slash-commands become `/task-rescue` and `/task-rescue-audit`; behavior is byte-identical to before (pure rename + vocabulary), so any orchestrator logic that keys on the skill's *output* is unaffected — only the invoked name changes.

## 4. What to do

1. Point-read `skills/docs/reserved-words.md` (mandated by the root CLAUDE.md now).
2. Sweep the orchestrator repo for the old vocabulary (§2) and conform its produced surfaces — its own "Language integration" pass. Tags stay legacy.
3. Update every live reference to `milestone-rescue` / `milestone-rescue-audit` → `task-rescue` / `task-rescue-audit`.
4. Verify: `grep -rIn 'milestone-rescue' orchestrator` → only frozen `.ai-factory` history remains; `/task-rescue` invokes correctly.

## 5. One-line statement

The skills family is now written in a formal reserved-words language (`skills/docs/reserved-words.md`, mandated from the root CLAUDE.md); the orchestrator speaks and stores that language, so conform its own surfaces — and follow the rename `milestone-rescue`/`-audit` → `task-rescue`/`task-rescue-audit` in every live reference.
