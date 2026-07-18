# Code Review: 8.1 — Docs and meta speak the language

## Scope

Docs-and-meta vocabulary pass: `milestone` → `task` across `docs/*.md`, `CLAUDE.md`, `.ai-factory/ARCHITECTURE.md`, plus one English synonym fix and one identifier reflection. This is static prose only — no `.py`, config, prompt, or runtime surface is touched, so there is nothing to break at runtime and no tests to run (the spec correctly declares zero tests; correctness is grep-verified).

I read the full diff of all twelve changed files, the governing spec (`.ai-factory/specs/trickster77777/27-docs-and-meta-speak-the-language.md`), and re-ran the spec's entire § Verify grep suite against the working tree.

## Verification results (all pass)

- `grep -rniE "\bmilestone" docs/*.md CLAUDE.md .ai-factory/ARCHITECTURE.md` → **0** hits.
- `grep -rniE "\bmilestone" README.md` → **0** hits; `README.md` is absent from the diff (verify-only, untouched as required).
- `grep -rni 'spec note' docs/*.md CLAUDE.md .ai-factory/ARCHITECTURE.md` → **0** hits.
- `grep -c 'process_milestone' CLAUDE.md` → **0**; `grep -c 'process_task' CLAUDE.md` → **1** (§ 5 identifier reflection applied).
- `grep -c 'кросс-милстоунная' docs/phase-sessions.md` → **0**; `grep -c 'межзадачная' docs/phase-sessions.md` → **2** (§ 4 both occurrences).
- Features hashes `48e435d de7849d`, `e50159f`, `b214041` all present and byte-identical.
- `git diff` touches exactly the twelve named files — no more, no less; `docs/future/*` absent.

## Correctness checks

- **Russian inflection is correct.** Nominative plural uses the velar form `task-и` everywhere (configuration, context-model, how-it-works, target-project, test-mode, workflow); genitive `task-ов` and instrumental `task-ами` retained unchanged. `grep 'task-ы\|таскы'` → 0 hits — the «таскы» error the spec warns against does not occur.
- **Gender/case agreement holds.** "таск" is masculine like "милстоун", so surrounding agreements ("каждый task", "завершён", "не сошёлся", "третьему task", "нового task") remain grammatical after the substring swap.
- **Config-token ground-truth corrections applied** (`configuration.md` JSON line, alert-type table, and the second example array): `milestone-fail`/`milestone` → `task-fail`/`task`, matching the live code since spec 25. `stop`/`done` left alone.
- **Protocol literals preserved byte-identical:** `## Deferred observations`, `PLAN_REVIEW_PASS`/`REVIEW_PASS`, and the `Spec:` / `Governing spec:` tags (verified in `context-model.md:20,21,35`) are untouched even where surrounding prose conforms.
- **Rescue-skill names untouched:** `/task-rescue` and `/task-rescue-audit` unchanged on `how-it-works.md:25` and `non-convergence.md:37`; only the bare-word "milestone" prose sharing the non-convergence line conforms. `how-it-works.md:25` correctly received no edit.
- **`phase` untouched**, commit hashes untouched, no typography sweep — matching every guard.

No correctness, security, or runtime-breakage issues found. The implementation is a faithful, complete application of the spec's per-line map.

## Deferred observations

- **`docs/context-model.md:20` retains the Russian term "спек-нота / Спек-ноты"** ("...путь к спек-ноте задачи ... Спек-ноты живут в `specs/`..."). This is the Russian rendering of the same concept the English synonym fix retired ("spec notes" → "task specs"). It is **correctly out of scope for 8.1** — the spec bounds the synonym fix to exactly one English line (`migrate-to-named-roadmap.md:23`) and states "Nothing else in the docs' prose changes spelling"; the verify grep targets only the English `spec note`. Retiring the Cyrillic term would require an un-authorized translation decision (спек-нота → таск-спека / спецификация задачи). Flagged for the phase owner as a possible follow-up if full Russian-side synonym conformance is later desired — not a defect in this task.

REVIEW_PASS
