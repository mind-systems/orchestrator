# Handoff — the language contract softened to naming-only; re-target the conformance direction before running it

> Cross-repo handoff from the skills side, 2026-07-18. **Supersedes [handoff 06](06-reserved-words-language-and-rescue-rename-orchestrator-side.md) §§ 1–2 and its kebab-form table entirely**; 06's protocol-literal and frozen-history guards stand. The orchestrator's "Reserved-words language conformance" direction (phases 5–8 of `roadmaps/trickster77777.md`) was planned against 06 — part of it is still exactly right, part now prescribes work the contract no longer wants. Re-plan the affected lines and specs first; then run.

## 1. What changed on the skills side

The reserved-words contract was softened to **naming-only** (skills commit `94ad78d`, live in `skills/docs/reserved-words.md` + `skills/docs/using-the-language.md`, both imported into the root `CLAUDE.md` — every session in the family loads them):

- **Reserved is the meaning, not the spelling.** The registry binds which *name* a concept goes by — one meaning one word, one word one meaning. It no longer prescribes a token form: kebab-case is dropped, terms are ordinary English — `task spec`, `contract line`, `PASS signal`, `deferred observations`, `named roadmap`, `owner line`, `governing spec`.
- **Typography is never swept.** A hyphen or a capital is not a defect. Attributive compounds keep their grammatical hyphen ("named-roadmap resolution order", "deferred-observations section format" as modifiers are correct English); noun uses are plain ("the task spec", "a deferred observation"). Existing kebab spellings in prose are legal variants — corrected opportunistically, never campaigned against.
- **Fixed form survives only on the machine axis** — exactly the things 06 already froze: skill/directory names, file paths, frontmatter fields, and the protocol literals (`## Deferred observations`, `- Affects: …`, `PLAN_REVIEW_PASS`/`REVIEW_PASS`, the `Spec:`/`Governing spec:` tags, `.ai-factory/specs/`). That part of 06 is unchanged.
- **Bonus, unrelated to vocabulary:** the global CLAUDE.md now recognizes two doc modes — a **governing spec leads code** (intended behavior, code verified against it) vs a description that lags it. The orchestrator's doc-first ТЗ practice (`docs/configuration.md` § Оверлей, Phase 3) is now the globally sanctioned default, not an owner override.

## 2. What in phases 5–8 is still exactly right — run as planned

Every **`milestone` → `task`** move is synonym retirement — the core of the naming contract — and survives untouched:

- **5.1** code identifiers (`Milestone` dataclass, `process_milestone`, the locals, `state.milestones_done`, tests) — valid, resume-safety anchors and all.
- **6.1** runtime surface (Telegram tokens `milestone`/`milestone-fail` → `task`/`task-fail`, message text, run summary) — valid, including the accepted config-token break.
- **7.1** prompts' `milestone` → `task` — valid. The plan-altitude reading of `task` (`## Tasks`, `**Task N:**` untouched) — valid, that reasoning is now § "The one rule" verbatim.
- **8.1** docs/meta `milestone` → `task`, the Russian loanword inflection (`task-и`, not «таскы»), the `кросс-милстоунная` → `межзадачная` judgment call — all valid.
- **8.2** the rescue rename itself — valid (see § 4 for the new gate).
- All guards on protocol literals, legacy tags, frozen history, byte-stable resume — valid everywhere.

## 3. What is superseded — amend before running

The **hyphenation clauses** planned per 06's kebab table now prescribe the opposite of the contract:

- **Roadmap, direction preamble** (line 23–25) — reframe from "formal reserved-words language / canonical forms" to the naming-only contract.
- **Roadmap 7.1** — drop `"named roadmap"→"named-roadmap"` and the deferred-observations hyphenation clause (both spellings were already correct); `"full specification"→"full task-spec"` becomes → **"full task spec"** (the synonym fix stays, the spelling is plain).
- **Spec `trickster77777/26`** — the slice rows that hyphenate (`named roadmap`→`named-roadmap` on reviewer.md:23/56; "deferred observation" → "deferred-observations entry" rows 113/116) are dropped — the existing plain spellings are already conformant; `task-spec` targets become `task spec`.
- **Spec `trickster77777/27`** — § 3 "Reserved-form hyphenation of prose" is deleted wholesale except its one synonym row ("spec notes" → "task specs", plain); the § 1 framing "un-hyphenated reserved forms" is no longer a defect class. README's `PASS-signal` spelling is a legal variant, not a conformance credit — the verify pass just checks zero `milestone`.
- **Roadmap vision line** ("plans, implements, and reviews code **milestones**") — same synonym, ride it along with 8.1.
- Rule for all amendments: conform **word choice**, leave typography alone; "no change" is a legal per-line outcome.

## 4. The rescue rename — new coordinates

The rename is unchanged in substance (`milestone-rescue` → `task-rescue`, `milestone-rescue-audit` → `task-rescue-audit`; behavior identical; frozen history keeps old names). Its skills-side task moved: **Phase 16, task 16.1, spec `skills/.ai-factory/specs/71-rescue-skills-rename.md`** (11.1 / spec 64 no longer exist — the conformance phases 9–12 were re-planned as skills Phase 17). Re-point **8.2's gate**: run when skills 16.1 is `[x]` **and** `skills/src/skills/task-rescue*` exist on disk; cite the landed names, never the plan.

## 5. What to do

1. Point-read `skills/docs/reserved-words.md` and `skills/docs/using-the-language.md` fresh — they are short now and the contract's letter matters here.
2. Amend the four surfaces in § 3 (roadmap preamble + 7.1, specs 26 and 27, vision line) and 8.2's gate (§ 4).
3. Run phases 5–8 as amended. Nothing in phases 5, 6 needed re-planning — they can run first, unchanged.
4. Handoff 06 stays on disk untouched — frozen history; this handoff is its supersession record.

## 6. One-line statement

The reserved-words contract now binds word choice, not spelling — keep every `milestone`→`task` move and the rescue-rename (now gated on skills 16.1 / spec 71), drop every hyphenation clause planned per handoff 06, and never sweep typography.
