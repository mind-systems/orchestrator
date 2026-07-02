# Code Review: Prompts: drop DESCRIPTION.md reads

**Scope:** Prompt + docs change. `agents.py`/`main.py` expected untouched.
**Risk Level:** 🟢 Low

## What was checked

Ran `git diff HEAD` and `git status`, read every changed file in full (`planner.md`, `test-planner.md`, `implementer.md`, `docs/target-project.md`, `docs/how-it-works.md`, `docs/context-model.md`, `CLAUDE.md`), and re-ran the verification grep.

## Verification

- **DESCRIPTION sweep clean.** `grep -rn DESCRIPTION orchestrator/ docs/ CLAUDE.md` (excluding `.ai-factory/`) returns **zero** matches — every read reference is removed. Task 6's completeness gate holds.
- **No Python touched.** `agents.py` / `main.py` contain no DESCRIPTION references and are not in the diff — matches the "prompt+docs only" contract.
- **`implementer.md` renumbering correct.** Sub-steps are now contiguous `2.1 → 2.2 → 2.3 → 2.4 (AGENTS/ARCHITECTURE) → 2.5 (Move to next task)`; no dangling `2.6` and no other reference to the old numbers survives. The deleted `2.4: Update DESCRIPTION.md` block (which resurrected DESCRIPTION.md as "source of truth") is fully gone, taking the inner lines 87/94 with it.
- **`planner.md` Step 0 / Step 1.** DESCRIPTION block removed; the Step 1 skip line correctly reworded to "Skip if the project context already in hand is sufficient." ARCHITECTURE/RULES/"Follow mentions" blocks intact. No CLAUDE.md-read instruction was added anywhere (spec constraint honored).
- **`test-planner.md` Step 0.** DESCRIPTION block removed; remaining reads open cleanly with `**Read `.ai-factory/ARCHITECTURE.md`**`.
- **Docs.** Russian preserved in all three docs; `CLAUDE.md` English preserved. `target-project.md` requirement paragraph dropped (leaving ROADMAP + git required, ARCHITECTURE/RULES optional) and both phase-session enumerations trimmed. `context-model.md` line 19 now lists only ARCHITECTURE/RULES, consistent with line 18's framing of CLAUDE.md as the sole unconditional channel — no contradiction introduced.

## Minor observation (non-blocking)

- `orchestrator/prompts/planner.md:11` — Step 0 now opens with `**ALSO:** Read `.ai-factory/ARCHITECTURE.md`…`. The `**ALSO:**` was worded relative to the deleted `**FIRST:**` DESCRIPTION block, so it now reads as a dangling "also" with nothing preceding it. This is harmless prompt prose (the agent still reads ARCHITECTURE.md correctly) and the plan explicitly directed leaving these blocks verbatim; flagging only for a future cosmetic cleanup, not a correctness issue. `test-planner.md` does not have this quirk (its first read never carried an "ALSO" prefix).

No correctness, runtime, or security issues. The change is faithful to the plan and the spec.

REVIEW_PASS
