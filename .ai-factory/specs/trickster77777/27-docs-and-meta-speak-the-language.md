# Docs and meta speak the language

**Date:** 2026-07-14
**Source:** conversation context — editor decomposition of Phase 8, ratified by the architect (Phase 8 split into 8.1 ready-now / 8.2 gated, along the external-dependency boundary); amended 2026-07-18 per [handoff 07](../../handoffs/07-language-contract-softened-to-naming-only.md) — the contract is naming-only, so the hyphenation pass is dropped; only the synonym fixes remain

## Problem today

`docs/configuration.md`, `docs/context-model.md`, `docs/failures-and-halts.md`, `docs/how-it-works.md`, `docs/migrate-to-named-roadmap.md`, `docs/non-convergence.md`, `docs/phase-sessions.md`, `docs/target-project.md`, `docs/test-mode.md`, `docs/workflow.md`, `CLAUDE.md`, and `.ai-factory/ARCHITECTURE.md` still describe the pipeline with the retired word "milestone" and, in one place, the synonym "spec notes" where the vocabulary names the concept task specs. The docs' spellings of the reserved terms themselves ("named roadmap", "PASS signal", "governing spec") are ordinary English and already conformant — the contract binds word choice, never typography. `README.md` is already fully conformed (zero "milestone" hits; its `PASS-signal` spelling is a legal variant, not a conformance credit) — it needs no edit, only a verify pass.

Most `docs/*.md` files are majority-Russian prose (English headers, Russian body). "milestone" appears there as an English loanword carrying a Cyrillic case suffix via hyphen (`milestone-ов`, `milestone-ами`, `milestone-ы`). Renaming to "task" must carry the **correct** inflection for the new stem: "таск" is velar-stemmed, so its nominative plural is `task-и` (таски, not «таскы») — the `-ы`→`-и` shift is required, while `-ов`/`-ами` stay the same (see Guards).

This is prose-only, except for one place where a doc's inline example must track ground truth: `docs/configuration.md` shows literal JSON/table examples of the `telegram_alerts` config token vocabulary, which Phase 6 (task 6.1, spec 25) already renamed in the actual code (`milestone-fail`/`milestone` → `task-fail`/`task`). Left alone, these examples would misdescribe the current, real config format — so they conform too, as a ground-truth correction, not a new design decision.

**Precondition — 5.1 has landed by the time this task runs** (it sits after Phase 5 in roadmap order). The one code-identifier reference this task touches (`CLAUDE.md:85`, `` `process_milestone()` ``) is written against the **post-5.1** name, `` `process_task()` ``.

## The change

### 1. `milestone` → `task` (the roadmap unit), file by file

Rename `milestone`→`task` / `Milestone`→`Task`, carrying the correct Russian case ending for the new stem "таск" (velar): the nominative plural `milestone-ы`→`task-и` (таски — velar rule к→и, never «таскы»), while genitive `milestone-ов`→`task-ов` and instrumental `milestone-ами`→`task-ами` keep the same suffix. See Guards.

**`docs/configuration.md`** (Russian):

| Line | Change |
|---|---|
| 26 | "milestone объявляется" → "task объявляется" |
| 30 | "каждым milestone оркестратор" → "каждым task оркестратор"; "следующего milestone." → "следующего task." |
| 32 | "перед каждым milestone:" → "перед каждым task:" |
| 46 | "между milestone-ами" → "между task-ами"; "каждый milestone начинает" → "каждый task начинает" |
| 93 | "внутри milestone и внутри фазы" → "внутри task и внутри фазы" |
| 95 | "внутри milestone" → "внутри task" |
| 100 | "К третьему milestone фазы" → "К третьему task фазы" |
| 104 | "завершении milestone" → "завершении task" |
| 110 | JSON example `"telegram_alerts": ["milestone-fail", "stop", "milestone", "done"]` → `["task-fail", "stop", "task", "done"]` — **config-token vocabulary, already this way in the live code since spec 25; the doc example must match ground truth** |
| 120 | table cell `` `milestone-fail` `` → `` `task-fail` ``; prose "milestone не сошёлся" → "task не сошёлся" |
| 122 | table cell `` `milestone` `` → `` `task` ``; "Milestone успешно завершён" → "Task успешно завершён" |
| 123 | "Все milestone-ы в роадмапе выполнены" → "Все task-и в роадмапе выполнены" |
| 125 | example array `` `["milestone-fail", "stop", "done"]` `` → `` `["task-fail", "stop", "done"]` `` — same config-token ground-truth correction as line 110 |

**`docs/context-model.md`** (Russian):

| Line | Change |
|---|---|
| 3 | "контракт-строку milestone и путь" → "контракт-строку task и путь" |
| 7 | "описание milestone (контракт-строка целиком)" → "описание task (контракт-строка целиком)" |
| 21 | "соседние milestone-ы" → "соседние task-и" |
| 22 | "Сессия внутри milestone" → "Сессия внутри task" |
| 28 | "между milestone-ами фазы" → "между task-ами фазы"; "к последнему milestone в префиксе" → "к последнему task в префиксе" |
| 29 | "На каждый milestone в память" → "На каждый task в память" |
| 31 | "растёт с каждым milestone независимо" → "растёт с каждым task независимо" |

**`docs/failures-and-halts.md`** (Russian):

| Line | Change |
|---|---|
| 7 | "milestone не сошёлся" → "task не сошёлся"; "milestone объявляется несошедшимся" → "task объявляется несошедшимся" |
| 9 | "текущий milestone мог быть" → "текущий task мог быть" |
| 15 | "«провалить» milestone нет" → "«провалить» task нет" |
| 18 | "не с начала milestone" → "не с начала task" |
| 20 | "Несошедшийся milestone не помечается" → "Несошедшийся task не помечается" |
| 26 | "на границе milestone, до начала" → "на границе task, до начала" |
| 29 | "текущему milestone завершиться" → "текущему task завершиться" |

**`docs/how-it-works.md`** (Russian; carries the two gated skill-name refs, see Guards):

| Line | Change |
|---|---|
| 5 | "Каждый milestone проходит через две фазы" → "Каждый task проходит через две фазы" |
| 9 | "это отказ milestone" → "это отказ task" |
| 21 | "прервался в середине milestone" → "прервался в середине task" |
| 25 | **No change.** The skill name on this line is already `` `/task-rescue` `` (task 8.2 ran first, doc-first decision) — no "milestone" remains here. Leave the whole line untouched. |
| 27 | "уже завершённого milestone и пропускается" → "уже завершённого task и пропускается"; "недоделанного milestone" → "недоделанного task" |
| 31 | "группирует milestone-ы по фазам" → "группирует task-и по фазам"; "каждый следующий milestone продолжает" → "каждый следующий task продолжает" |
| 33 | "к третьему milestone фазы" → "к третьему task фазы" |
| 35 | "между milestone-ами" → "между task-ами"; "следующий milestone стартует" → "следующий task стартует" |
| 37 | "каждый milestone начинает" → "каждый task начинает" |
| 41 | "Перед каждым milestone оркестратор" → "Перед каждым task оркестратор"; "до начала нового milestone." → "до начала нового task." |
| 43 | "на каждый milestone." → "на каждый task." |
| 55 | "вне рамок milestone." → "вне рамок task." The quoted `` `## Deferred observations` `` on this same line is a protocol literal — stays byte-identical (see Guards). |

**`docs/migrate-to-named-roadmap.md`** (English, 0 "milestone" hits — one synonym fix only, see § 3).

**`docs/non-convergence.md`** (Russian; carries the two gated skill-name refs):

| Line | Change |
|---|---|
| 37 | Only the bare prose "сошёлся ли milestone через понимание" → "сошёлся ли task через понимание" changes. The two skill names on the same line are already `` `/task-rescue` `` and `` `/task-rescue-audit` `` (task 8.2 ran first, doc-first decision) and stay untouched — the bare word is the line's only remaining "milestone" substring. |

**`docs/phase-sessions.md`** (Russian; also carries the "кросс-милстоунная" judgment call, see § 4):

| Line | Change |
|---|---|
| 3 | "между milestone-ами внутри одной фазы" → "между task-ами внутри одной фазы" |
| 7 | "к третьему milestone планировщик" → "к третьему task планировщик"; **plus** "кросс-милстоунная память" → "межзадачная память" (§ 4) |
| 37 | heading "на каждый milestone" → "на каждый task" |
| 39 | "(7 milestone-ов)" → "(7 task-ов)" |
| 41 | "к последнему milestone тащит" → "к последнему task тащит"; "по числу milestone-ов." → "по числу task-ов."; "каждый milestone стартует" → "каждый task стартует" |
| 47 | "слабосвязанных milestone-ов" → "слабосвязанных task-ов"; **plus** "кросс-милстоунная память" → "межзадачная память" (§ 4, second occurrence) |
| 53 | "в раннем milestone неочевидно" → "в раннем task неочевидно" |

**`docs/target-project.md`** (Russian):

| Line | Change |
|---|---|
| 7 | "список milestone-ов в формате" → "список task-ов в формате" |
| 17 | "## Формат milestone-ов" → "## Формат task-ов" |
| 19 | "Строка milestone должна выглядеть" → "Строка task должна выглядеть" |
| 29 | "Milestone-ы можно группировать" → "Task-и можно группировать" |
| 42 | "через все milestone-ы" → "через все task-и" |
| 44 | "все milestone-ы тогда идут" → "все task-и тогда идут" |
| 48 | "после определённого milestone, вставьте" → "после определённого task, вставьте" |
| 66 | "коммит следующего milestone." → "коммит следующего task." |

**`docs/test-mode.md`** (Russian):

| Line | Change |
|---|---|
| 19 | "exit code 0 — milestone завершён" → "exit code 0 — task завершён" |
| 25 | "## Формат milestone-ов" → "## Формат task-ов" |
| 27 | "Milestone-ы для `test` режима" → "Task-и для `test` режима" |
| 42 | "После каждого milestone делается git commit" → "После каждого task делается git commit" |

**`docs/workflow.md`** (Russian):

| Line | Change |
|---|---|
| 11 | "каждый milestone должен делать" → "каждый task должен делать" |
| 13 | "Хороший milestone выглядит так:" → "Хороший task выглядит так:" |
| 28 | "обрабатывает milestone-ы по одному" → "обрабатывает task-и по одному"; "После каждого milestone задача" → "После каждого task задача" |
| 34 | "выполненных milestone-ов стоит" → "выполненных task-ов стоит" |

**`CLAUDE.md`** (English):

| Line | Change |
|---|---|
| 14 | "# Plan + implement milestones" → "# Plan + implement tasks" |
| 17 | "# Write tests for milestones from ROADMAP_TESTS.md" → "# Write tests for tasks from ROADMAP_TESTS.md" |
| 36 | "what counts as a milestone failure" → "what counts as a task failure" |
| 46 | "that processes milestones from a target project's" → "that processes tasks from a target project's" |
| 53 | "Pipeline per milestone (`implement` mode):" → "Pipeline per task (`implement` mode):" |
| 63 | "Pipeline per milestone (`test` mode):" → "Pipeline per task (`test` mode):" |
| 81 | "roadmap/milestone format" → "roadmap/task format" |
| 85 | (identifier reflection, see § 5) |

**`.ai-factory/ARCHITECTURE.md`** (English):

| Line | Change |
|---|---|
| 21 | "the unified milestone pipeline" → "the unified task pipeline" |
| 56 | "or milestones." → "or tasks." |
| 127 | `## Features` row: "Crash recovery — mid-milestone resume" → "Crash recovery — mid-task resume"; hash `48e435d de7849d` **unchanged** |
| 131 | "Auto-push to remote after milestone" → "Auto-push to remote after task"; hash `e50159f` **unchanged** |
| 134 | "Per-milestone usage guard" → "Per-task usage guard"; hash `b214041` **unchanged** |

**Ratified decision on the `## Features` rows (127, 131, 134):** these are compacted history anchored to commit hashes (`reserved-words.md` § "Features"). The hashes are the actual anchor and are never touched by any vocabulary pass. Only the row's descriptive label — which is prose describing what the commit did, not a quotation of code at the time — conforms, same as any other doc prose. This mirrors the fact that a newer Features row already uses the conformed form ("Deferred-observations review channel", line 136) sitting next to these un-conformed rows — the table is a living doc kept in the current vocabulary, not a frozen historical stratum like a ROADMAP `[x]` line.

### 2. `README.md` — verify only

Already conformed: 0 "milestone" hits; its `PASS-signal` spelling (line 5, ×2) is a legal variant the naming contract does not police. No edit. Include it in the final verify pass to confirm it stays that way.

### 3. Synonym fix in prose

One synonym retires — "spec notes" for what the vocabulary names task specs:

| File:Line | Current | New |
|---|---|---|
| `docs/migrate-to-named-roadmap.md:23` | "move the roadmap's spec notes there" | "move the roadmap's task specs there" |

Nothing else in the docs' prose changes spelling: "named roadmap", "PASS signals", "governing spec" as free prose are the registry names written in ordinary English — no hyphenation pass, no text swept for typography. The protocol-literal `` `Spec:` `` and `` `Governing spec:` `` **tags** stay legacy, untouched, everywhere (incl. `docs/context-model.md:21,35`).

### 4. Judgment call: `docs/phase-sessions.md`'s transliterated "кросс-милстоунная"

Two occurrences (lines 7, 47) use "кросс-милстоунная" — a fully Cyrillic-transliterated adjective derived from "milestone" (милстоун + adjective suffix), not the Latin-loanword-plus-hyphen pattern used everywhere else in these docs. A mechanical substring rename does not apply here (there is no Latin "milestone" substring to swap). `docs/context-model.md` already has an established native-Russian equivalent for the same concept — "межзадачная" / "межзадачных" ("inter-task", from "задача" = task) at lines 20 and 29. This task conforms `docs/phase-sessions.md`'s two "кросс-милстоунная" instances to that same existing term, "межзадачная", rather than inventing a new transliteration from "task" (which would produce an awkward, unprecedented word). This is a judgment call, not a mechanical rename — flagged here for the record; if the phase owner prefers a different resolution, this is the one line item to revisit.

### 5. Reflect the Phase-5 renamed identifier

| File:Line | Current | New |
|---|---|---|
| `CLAUDE.md:85` | "when instantiating agents in `` `process_milestone()` ``." | "when instantiating agents in `` `process_task()` ``." |

## Guards

- **Inflect the loanword correctly, not a blind suffix copy.** "таск" (task) is a velar stem — its nominative plural takes `-и`, so `milestone-ы`→`task-и` (таски, never «таскы»). Genitive-plural `-ов` and instrumental `-ами` are spelled the same for both stems, so `milestone-ов`→`task-ов`, `milestone-ами`→`task-ами`. Do not translate the sentence into native Russian; only inflect the loanword correctly (as the docs already do for `Implementer'у`).
- **The `кросс-милстоунная` → `межзадачная` swap (§ 4) is the one place a native Russian term replaces the loanword** — it aligns to an existing term elsewhere in the docs. Everywhere else, inflect `task` per the rule above.
- **Protocol literals stay legacy, byte-identical.** `` `## Deferred observations` `` (quoted at `docs/how-it-works.md:55`), `` `PLAN_REVIEW_PASS` ``/`` `REVIEW_PASS` `` (quoted at `docs/how-it-works.md:7,47,53` and `docs/non-convergence.md:3`), and the `` `Spec:` ``/`` `Governing spec:` `` tags (quoted throughout) are mechanism, not vocabulary — never rename these, even though the surrounding prose about them does conform.
- **Leave the two rescue-skill invocation names untouched.** `` `/task-rescue` `` and `` `/task-rescue-audit` `` at `docs/how-it-works.md:25` and `docs/non-convergence.md:37` are task 8.2's surface, already placed by it (doc-first). This task conforms only the bare-word "milestone" prose that happens to share a line with them (`docs/non-convergence.md:37` only — `docs/how-it-works.md:25` has no bare-word instance and gets no edit at all).
- **Typography is never swept.** The contract binds word choice, not spelling: "named roadmap", "PASS signal", "governing spec", link texts, and every other reserved term in prose keep their existing ordinary-English form — a hyphen or a capital is not a defect, and "no change" is a legal per-line outcome.
- **`phase` stays `phase` everywhere** — it is a real, correctly-used concept in every file here (the cross-phase persistent planner session, the roadmap phase header), never a collision to resolve. Do not touch it.
- **Commit hashes in `.ai-factory/ARCHITECTURE.md`'s `## Features` table are byte-identical** — only the row's prose label conforms (see § 1's ratified decision).
- Do not touch `docs/future/run-context-refactor.md` — out of the named file list, and it has zero "milestone" hits anyway.
- Do not touch any `.py` file, config, or the prompt files — those are Phases 5, 6, and 7 respectively, already landed or specced separately.

## Verify

- `grep -rniE "\bmilestone" docs/*.md CLAUDE.md .ai-factory/ARCHITECTURE.md` → zero hits (task 8.2 already renamed the skill-name substrings; this task removes every remaining bare-word instance).
- `grep -rniE "\bmilestone" README.md` → zero hits (unchanged from before this task).
- `grep -rni 'spec note' docs/*.md CLAUDE.md .ai-factory/ARCHITECTURE.md` → zero hits (the one retired synonym; existing "named roadmap" / "PASS signal" / "governing spec" spellings are conformant and not grepped for).
- `grep -n 'process_milestone' CLAUDE.md` → zero hits; `grep -n 'process_task' CLAUDE.md` → one hit.
- `grep -n 'кросс-милстоунная' docs/phase-sessions.md` → zero hits; `grep -c 'межзадачная' docs/phase-sessions.md` → 2.
- `.ai-factory/ARCHITECTURE.md` Features table: `grep -n '48e435d de7849d\|e50159f\|b214041' .ai-factory/ARCHITECTURE.md` shows the same three hashes, unchanged.
- `git diff` touches only the twelve files named in Problem today — `README.md` and `docs/future/*` absent from the diff.

## What NOT to do

- Do not touch the `/task-rescue` / `/task-rescue-audit` skill names — task 8.2 already placed them.
- Do not touch `## Deferred observations`, `PLAN_REVIEW_PASS`, `REVIEW_PASS`, or any `Spec:`/`Governing spec:` tag.
- Do not touch commit hashes in `.ai-factory/ARCHITECTURE.md`'s Features table.
- Do not decline or translate the Russian loanword suffixes — substring rename only.
- Do not hyphenate or re-case any prose — no typography sweep; the only spelling-level edits in this task are the `milestone`→`task` renames, the "spec notes"→"task specs" synonym, and § 4's «межзадачная».
- Do not touch `README.md` (already conformed) or `docs/future/run-context-refactor.md` (out of scope, no hits).
- Do not touch any `.py` file, `orchestrator.json`/`.example`, or the four `orchestrator/prompts/*.md` files.

## Tests

None. All twelve files are static prose (docs, project meta) — a loud-failure surface with nothing to parse them at runtime. Correctness is verified by the greps above, not a test run.
