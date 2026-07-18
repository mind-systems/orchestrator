# Plan: 8.1 — Docs and meta speak the language

## Context
Conform the retired word `milestone` → the reserved word `task` across the orchestrator's docs and project meta (Russian-majority `docs/*.md`, English `CLAUDE.md`, `.ai-factory/ARCHITECTURE.md`), inflecting the Russian loanword correctly, retiring one synonym ("spec notes" → "task specs"), and reflecting the post-5.1 identifier `process_task()`. Word choice only — no typography sweep, protocol literals and tags left legacy.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Ground rules (apply to every task below)
The spec `.ai-factory/specs/trickster77777/27-docs-and-meta-speak-the-language.md` carries the authoritative per-line edit map — follow it exactly; it was verified against the live files and matches. Across all tasks:
- **Russian inflection:** velar stem "таск" — nominative plural `milestone-ы` → `task-и` (таски, never «таскы»); genitive `-ов` and instrumental `-ами` stay (`task-ов`, `task-ами`). Substring rename of the Latin loanword only — do not translate the sentence into native Russian.
- **Protocol literals stay byte-identical:** `` `## Deferred observations` ``, `` `PLAN_REVIEW_PASS` `` / `` `REVIEW_PASS` ``, and the `` `Spec:` `` / `` `Governing spec:` `` tags — never rename, even when surrounding prose conforms.
- **Leave `/task-rescue` / `/task-rescue-audit` skill names untouched** (task 8.2 placed them; only bare-word "milestone" prose sharing their line is in scope).
- **No typography sweep:** "named roadmap", "PASS signal", "governing spec" and every other reserved term in prose keep their existing ordinary-English spelling. "No change" is a legal per-line outcome.
- **`phase` stays `phase` everywhere** — correctly used, never a collision.
- **Commit hashes in ARCHITECTURE.md's `## Features` table are byte-identical** — only the row's prose label conforms.
- Do NOT touch any `.py`, config (`orchestrator.json`/`.example`), the `orchestrator/prompts/*.md`, `README.md`, or `docs/future/*`.

## Tasks

### Phase 1: Russian docs vocabulary pass

- [x] **Task 1: Conform `docs/configuration.md`**
  Files: `docs/configuration.md`
  Apply the spec § 1 line map (lines 26, 30, 32, 46, 93, 95, 100, 104, 120, 122, 123). Prose `milestone`→`task` with correct inflection (line 46 `milestone-ами`→`task-ами`; line 123 `milestone-ы`→`task-и`). Lines 110 and 125 are **config-token ground-truth corrections**, already this way in live code since spec 25: `"milestone-fail"`→`"task-fail"` and `"milestone"`→`"task"` inside the JSON/array examples; line 120/122 table cells `` `milestone-fail` ``→`` `task-fail` `` and `` `milestone` ``→`` `task` ``. Leave the `stop`/`done` tokens alone.

- [x] **Task 2: Conform `docs/context-model.md`**
  Files: `docs/context-model.md`
  Apply spec § 1 line map (lines 3, 7, 21, 22, 28, 29, 31). Inflect: line 21 `milestone-ы`→`task-и`, line 28 `milestone-ами`→`task-ами`. Do NOT touch the `` `Governing spec:` `` tag on line 21 or the already-conformant "Межзадачная память" on line 29.

- [x] **Task 3: Conform `docs/failures-and-halts.md`**
  Files: `docs/failures-and-halts.md`
  Apply spec § 1 line map (lines 7, 9, 15, 18, 20, 26, 29) — all bare-word prose `milestone`→`task`.

- [x] **Task 4: Conform `docs/how-it-works.md`**
  Files: `docs/how-it-works.md`
  Apply spec § 1 line map (lines 5, 9, 21, 27, 31, 33, 35, 37, 41, 43, 55). Inflect: line 31 `milestone-ы`→`task-и`, line 35 `milestone-ами`→`task-ами`. **Line 25 gets no edit at all** (skill name already `/task-rescue`, no bare word). On line 55 the quoted `` `## Deferred observations` `` stays byte-identical — only the surrounding "вне рамок milestone" → "вне рамок task" conforms.

- [x] **Task 5: Conform `docs/non-convergence.md`**
  Files: `docs/non-convergence.md`
  Line 37 only: the bare prose "сошёлся ли milestone через понимание" → "сошёлся ли task через понимание". The two skill names `` `/task-rescue` `` and `` `/task-rescue-audit` `` on the same line stay untouched.

- [x] **Task 6: Conform `docs/phase-sessions.md` (incl. the § 4 judgment call)**
  Files: `docs/phase-sessions.md`
  Apply spec § 1 line map (lines 3, 7, 37, 39, 41, 47, 53). Inflect: line 3 `milestone-ами`→`task-ами`; line 39 `(7 milestone-ов)`→`(7 task-ов)`; line 41 `по числу milestone-ов`→`по числу task-ов`; line 47 `слабосвязанных milestone-ов`→`слабосвязанных task-ов`. **§ 4 (both occurrences, lines 7 and 47):** the transliterated adjective "кросс-милстоунная память" → "межзадачная память", aligning to the existing native term already used in `docs/context-model.md`. This is the one place a native Russian term replaces the loanword.

- [x] **Task 7: Conform `docs/target-project.md`**
  Files: `docs/target-project.md`
  Apply spec § 1 line map (lines 7, 17, 19, 29, 42, 44, 48, 66). Inflect: line 7 `milestone-ов`→`task-ов`; heading line 17 `## Формат milestone-ов`→`## Формат task-ов`; line 29 `Milestone-ы`→`Task-и`; lines 42, 44 `milestone-ы`→`task-и`.

- [x] **Task 8: Conform `docs/test-mode.md`**
  Files: `docs/test-mode.md`
  Apply spec § 1 line map (lines 19, 25, 27, 42). Heading line 25 `## Формат milestone-ов`→`## Формат task-ов`; line 27 `Milestone-ы`→`Task-и`.

- [x] **Task 9: Conform `docs/workflow.md`**
  Files: `docs/workflow.md`
  Apply spec § 1 line map (lines 11, 13, 28, 34). Inflect: line 28 `milestone-ы`→`task-и`; line 34 `milestone-ов`→`task-ов`.

- [x] **Task 10: Synonym fix in `docs/migrate-to-named-roadmap.md`**
  Files: `docs/migrate-to-named-roadmap.md`
  Zero "milestone" hits — one synonym change only (spec § 3), line 23: "move the roadmap's spec notes there" → "move the roadmap's task specs there". Leave the `` `Spec:` `` tag reference on the same line untouched.

### Phase 2: English project meta

- [x] **Task 11: Conform `CLAUDE.md` (incl. the post-5.1 identifier)**
  Files: `CLAUDE.md`
  Apply spec § 1 line map (lines 14, 17, 36, 46, 53, 63, 81): prose/comment `milestone(s)`→`task(s)`, e.g. "# Plan + implement milestones"→"# Plan + implement tasks", "Pipeline per milestone"→"Pipeline per task", "roadmap/milestone format"→"roadmap/task format". **Line 85 (spec § 5):** reflect the Phase-5 rename — `` `process_milestone()` `` → `` `process_task()` `` (the identifier already exists post-5.1).

- [x] **Task 12: Conform `.ai-factory/ARCHITECTURE.md` (Features labels, hashes stay)**
  Files: `.ai-factory/ARCHITECTURE.md`
  Apply spec § 1 line map (lines 21, 56, 127, 131, 134): line 21 "the unified milestone pipeline"→"the unified task pipeline"; line 56 "or milestones."→"or tasks."; **`## Features` rows 127/131/134** — conform only the descriptive label ("mid-milestone resume"→"mid-task resume", "after milestone"→"after task", "Per-milestone usage guard"→"Per-task usage guard"); the commit hashes `48e435d de7849d`, `e50159f`, `b214041` stay byte-identical.

### Phase 3: Verify

- [x] **Task 13: Run the verification grep suite** (depends on Tasks 1-12)
  Files: (read-only verification — no edits)
  Run the spec § Verify checks and confirm each: `grep -rniE "\bmilestone" docs/*.md CLAUDE.md .ai-factory/ARCHITECTURE.md` → zero hits; `grep -rniE "\bmilestone" README.md` → zero hits (README is verify-only, must remain unedited); `grep -rni 'spec note' docs/*.md CLAUDE.md .ai-factory/ARCHITECTURE.md` → zero hits; `grep -n 'process_milestone' CLAUDE.md` → zero, `grep -n 'process_task' CLAUDE.md` → one; `grep -n 'кросс-милстоунная' docs/phase-sessions.md` → zero, `grep -c 'межзадачная' docs/phase-sessions.md` → 2; `grep -n '48e435d de7849d\|e50159f\|b214041' .ai-factory/ARCHITECTURE.md` → the same three hashes present. Confirm `git diff` touches only the twelve named files — `README.md` and `docs/future/*` absent. If any check fails, fix the offending line and re-run.

## Commit Plan
- **Commit 1** (after tasks 1-4): "Conform milestone to task across configuration, context-model, failures-and-halts, how-it-works docs"
- **Commit 2** (after tasks 5-9): "Conform milestone to task across non-convergence, phase-sessions, target-project, test-mode, workflow docs"
- **Commit 3** (after tasks 10-13): "Conform project meta to task vocabulary and verify the pass"
