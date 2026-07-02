# Plan: Prompts: drop DESCRIPTION.md reads

## Context
Retire DESCRIPTION.md across the toolchain: the target project's CLAUDE.md (which the claude CLI injects into every agent run) already carries the same facts, so no prompt needs to read DESCRIPTION.md. This is a prompt+docs change; `agents.py`/`main.py` stay untouched, and target-project DESCRIPTION.md files are not deleted.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes (edits to existing docs only)

## Notes for the implementer
- **All `docs/*.md` files and `docs/target-project.md` are written in Russian.** Preserve Russian when editing them. The prompt files (`orchestrator/prompts/*.md`) are in English.
- Do NOT add any "read CLAUDE.md" instruction anywhere — the CLI injects CLAUDE.md unconditionally.
- Keep every `ARCHITECTURE.md` and `RULES.md` read intact; only DESCRIPTION.md references are removed.
- Spec: `.ai-factory/notes/04-drop-description-reads.md`.

## Tasks

### Phase 1: Prompts

- [x] **Task 1: Drop DESCRIPTION.md from `planner.md`**
  Files: `orchestrator/prompts/planner.md`
  In Step 0, delete the entire `**FIRST:** Read `.ai-factory/DESCRIPTION.md` if it exists…` block (the heading line plus its four bullets, lines ~11-15). Leave the `**ALSO:** Read `.ai-factory/ARCHITECTURE.md`…` and `**ALSO:** Read `.ai-factory/RULES.md`…` blocks and the "Follow mentions" block unchanged. In Step 1 (Quick Reconnaissance), reword the skip line "Skip if `.ai-factory/DESCRIPTION.md` already provides sufficient context." → "Skip if the project context already in hand is sufficient." Do not add a CLAUDE.md read instruction.

- [x] **Task 2: Drop DESCRIPTION.md from `test-planner.md`**
  Files: `orchestrator/prompts/test-planner.md`
  In Step 0, delete the `**Read `.ai-factory/DESCRIPTION.md`** if it exists…` block (heading line plus its two bullets, lines ~11-13). Leave the ARCHITECTURE.md / RULES.md read blocks and the "Follow mentions" block intact.

- [x] **Task 3: Remove DESCRIPTION.md stragglers from `implementer.md`**
  Files: `orchestrator/prompts/implementer.md`
  Grep flagged `implementer.md` as a straggler (the note assumed it referenced only RULES/ROADMAP). Remove both DESCRIPTION.md touchpoints: (a) in Step 0, delete the `**Read `.ai-factory/DESCRIPTION.md`** if it exists…` block (heading plus its three bullets, lines ~11-14), keeping the ARCHITECTURE.md, RULES.md, and patches read blocks; (b) delete sub-step `**2.4: Update .ai-factory/DESCRIPTION.md if needed**` in full (lines ~79-94) — it resurrects DESCRIPTION.md as "source of truth," contradicting retirement. Renumber the following sub-steps (`2.5` → `2.4`, `2.6` → `2.5`) so numbering stays contiguous. Do not touch the AGENTS.md/ARCHITECTURE.md update sub-step content beyond its number.

### Phase 2: Docs

- [x] **Task 4: Update `docs/target-project.md`** (depends on nothing)
  Files: `docs/target-project.md`
  Delete the `DESCRIPTION.md` requirement paragraph (line ~11). The required set becomes `ROADMAP.md` + git; `ARCHITECTURE.md` / `RULES.md` remain optional (leave their paragraphs as-is). In the phase-session paragraph (line ~42), drop `DESCRIPTION.md` from the "не тратит токены на повторное чтение `DESCRIPTION.md`, `ARCHITECTURE.md`…" enumeration so it lists only `ARCHITECTURE.md` and prior-plan context. Keep the text Russian.

- [x] **Task 5: Grep-sweep remaining docs** (depends on Task 4)
  Files: `docs/how-it-works.md`, `docs/context-model.md`, `CLAUDE.md`
  Remove/reword every remaining DESCRIPTION reference: in `docs/how-it-works.md` (line ~31) drop `DESCRIPTION.md` from the "планировщик уже знает `DESCRIPTION.md`, `ARCHITECTURE.md`…" sentence; in `docs/context-model.md` (line ~19) remove `DESCRIPTION.md` from the "обязательное чтение по Step 0" bullet, leaving `ARCHITECTURE.md`, `RULES.md`; in `CLAUDE.md` (line ~74) drop `DESCRIPTION` from the `` `DESCRIPTION`/`ARCHITECTURE`/`RULES` files `` list in the "Target project requirements" section. Preserve each file's existing language (docs Russian, CLAUDE.md English). Do not introduce any CLAUDE.md-read instruction.

- [x] **Task 6: Verify completeness by grep** (depends on Tasks 1-5)
  Files: (no edits — verification)
  Run `grep -rn DESCRIPTION orchestrator/ docs/ CLAUDE.md` (excluding `.ai-factory/`). Confirm no DESCRIPTION references remain in prompts or docs, and confirm `agents.py`/`main.py` were never in the results (prompt+docs-only change, as expected). If any straggler surfaces, remove it consistent with the tasks above.

## Commit Plan
- **Commit 1** (after tasks 1-3): "Drop DESCRIPTION.md reads from agent prompts"
- **Commit 2** (after tasks 4-6): "Retire DESCRIPTION.md from target-project and context docs"
