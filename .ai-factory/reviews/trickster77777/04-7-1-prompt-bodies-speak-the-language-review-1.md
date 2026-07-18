# Review: 7.1 — Prompt bodies speak the language

## Scope
Prose-only vocabulary conformance across three agent prompts (`planner.md`, `test-planner.md`, `reviewer.md`): retire the synonym `milestone` for the reserved word `task`, plus "full specification" → "full task spec". No code, no parser, no runtime message. Verified against `.ai-factory/specs/trickster77777/26-prompt-bodies-speak-the-language.md` § "The change" / Guards / Verify.

## Verification

**All spec greps pass:**
- `grep -rniE "\bmilestone" orchestrator/prompts/*.md` → **zero hits** (case-insensitive, so no residual `Milestone` either).
- `grep -rn "full specification" orchestrator/prompts/*.md` → **zero hits** (synonym retired at `planner.md:22` and `test-planner.md:19`).
- `git diff HEAD` touches **only** the three prompt files — `implementer.md` and all `.py`/`docs`/`CLAUDE.md`/config are untouched.

**Substitution accuracy:** every row of the spec's three tables was applied exactly and nothing beyond them:
- `planner.md` — lines 3, 5, 21, 22, 24, 25, 48, 82, 85, 136, 143. Line 22 folds in "the full task spec". Line 136 renames only `milestone`; "test tasks" (plan-checklist meaning) correctly preserved.
- `test-planner.md` — lines 3, 5, 18, 19, 21, 22, 27 ("### Step 1: Read the Task"), 29, 38, 76, 125. Line 19 folds in "the full task spec".
- `reviewer.md` — lines 23, 24, 25, 112, 113, 114, 116. "named roadmap" correctly left as-is on line 23.

**Guards held (protocol literals byte-for-byte):**
- `## Deferred observations` (reviewer.md:106), `- Affects:` (reviewer.md:108), `PLAN_REVIEW_PASS` / `REVIEW_PASS` (reviewer.md:118–121) — unchanged, confirmed by grep.
- `Spec:` / `Governing spec:` tags (planner.md:22,24; test-planner.md:19,21; reviewer.md:24) — the tag tokens are preserved; only surrounding prose was reworded.

**Plan-checklist wording preserved:** `## Tasks` (planner.md:92), the `**Task N: <subject>**` format block, and `# Plan: <task title>` checklist wording are untouched — the plan-altitude `task` reads consistently, no collision introduced.

**Typography not swept:** "named roadmap" and "deferred observation(s)" keep their existing ordinary-English spelling, per the naming-only contract.

## Runtime risk
None. These files are static text read by the LLM agent at session start, not parsed by the orchestrator — a loud-failure surface with no silent-break path. No migrations, types, or state involved.

REVIEW_PASS
