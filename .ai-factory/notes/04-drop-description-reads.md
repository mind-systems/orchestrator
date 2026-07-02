# Prompts: drop DESCRIPTION.md — CLAUDE.md arrives with every agent run

**Date:** 2026-07-02
**Source:** conversation context (artifact-usefulness review)

## Key Findings

- DESCRIPTION.md is retired across the toolchain: it duplicated the target project's CLAUDE.md (stack, purpose, conventions), and every orchestrator agent runs via the claude CLI in the project cwd — CLAUDE.md is injected into each run unconditionally, so the facts arrive for free without any prompt instruction.
- The prompts currently read it: `planner.md` Step 0 ("**FIRST:** Read `.ai-factory/DESCRIPTION.md`…"), `test-planner.md` Step 0 (same block), `planner.md` Step 1 ("Skip if DESCRIPTION.md already provides sufficient context"). `reviewer.md` and `implementer.md` reference `RULES.md`/`ROADMAP.md` only — verify with a grep and fix any stragglers.

## Details

- **`planner.md` + `test-planner.md` Step 0:** delete the DESCRIPTION.md block. `ARCHITECTURE.md` and `RULES.md` reads stay. Do not add a "read CLAUDE.md" instruction — it is already in context.
- **`planner.md` Step 1:** the recon-skip condition "Skip if `.ai-factory/DESCRIPTION.md` already provides sufficient context" → "Skip if the project context already in hand is sufficient".
- **Docs:** `docs/target-project.md` — remove the DESCRIPTION.md requirement paragraph (the target project needs `ROADMAP.md` + git; `ARCHITECTURE.md`/`RULES.md` stay optional); sweep other docs pages with a grep for `DESCRIPTION`.
- Grep the whole repo (`grep -rn DESCRIPTION orchestrator/ docs/`) and clean every remaining reference; `agents.py`/`main.py` are expected to have none (prompt-only change), but verify.

## What NOT to do

- Do not touch `ARCHITECTURE.md` / `RULES.md` handling — they remain the hard-requirement reads.
- Do not add CLAUDE.md read instructions — the CLI injects it.
- Do not modify Python beyond what the grep proves necessary (expected: nothing).
- Do not delete DESCRIPTION.md files from any target project — reads retire, files die of natural causes.
