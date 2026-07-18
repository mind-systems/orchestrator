# Plan: 7.1 — Prompt bodies speak the language

## Context
Conform the three agent prompt bodies (`planner.md`, `test-planner.md`, `reviewer.md`) to the reserved word `task` — retiring the synonym `milestone` for the roadmap unit and one "full specification" → "full task spec" fix — so every plan and review the orchestrator produces speaks the shared vocabulary. Prose-only; protocol literals and the plan-checklist `task` wording stay byte-for-byte.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Conform the three prompt bodies

The prompt files live at `orchestrator/prompts/` relative to the repo root (i.e. `orchestrator/orchestrator/prompts/` from this checkout). All edits are the exact line-by-line substitutions enumerated in the spec's tables (`.ai-factory/specs/trickster77777/26-prompt-bodies-speak-the-language.md` § "The change") — the current file line numbers were confirmed to match those tables. Rename **only** the roadmap-unit sense of `milestone`/`Milestone` to `task`/`Task`; leave every plan-checklist `task`/`Task` (`## Tasks`, `**Task N:**`, "test tasks") untouched. Do not sweep typography — "named roadmap" and "deferred observation(s)" keep their existing ordinary-English spelling.

**Hard guard for all three files:** the protocol literals `## Deferred observations`, `- Affects:`, `PLAN_REVIEW_PASS`, `REVIEW_PASS`, and the `Spec:` / `Governing spec:` tags stay byte-for-byte unchanged (cross-repo shared surface, per the spec § Guards and skills handoff 21). Touch no `.py`, `docs/*.md`, `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, config, or `implementer.md`.

- [x] **Task 1: Conform `planner.md`**
  Files: `orchestrator/prompts/planner.md`
  Apply the 11 substitutions from the spec's `planner.md` table (lines 3, 5, 21, 22, 24, 25, 48, 82, 85, 136, 143): each `milestone` naming the roadmap unit → `task`, `<milestone title>` → `<task title>`, and line 22's "it is the full specification" → "the full task spec" (folds in the synonym fix). Line 136: rename only `milestone`; keep "test tasks" (plan-checklist meaning) as-is. Leave the `## Tasks` / `**Task N:**` checklist format, `Spec:`/`Governing spec:` tags, and all other prose untouched.

- [x] **Task 2: Conform `test-planner.md`**
  Files: `orchestrator/prompts/test-planner.md`
  Apply the 11 substitutions from the spec's `test-planner.md` table (lines 3, 5, 18, 19, 21, 22, 27, 29, 38, 76, 125): each roadmap-unit `milestone` → `task`, line 27 "### Step 1: Read the Milestone" → "### Step 1: Read the Task", `<milestone title>` → `<task title>`, and line 19's "it is the full specification" → "the full task spec". Leave the plan-checklist wording, `Spec:`/`Governing spec:` tags, and other prose untouched.

- [x] **Task 3: Conform `reviewer.md`**
  Files: `orchestrator/prompts/reviewer.md`
  Apply the 7 substitutions from the spec's `reviewer.md` table (lines 23, 24, 25, 112, 113, 114, 116): each roadmap-unit `milestone`/`milestone's` → `task`/`task's`, `<milestone title>` → `<task title>`. Line 23 renames only `milestone` — "named roadmap" stays. Do **not** touch the `## Deferred observations` heading, the `- Affects:` line, `PLAN_REVIEW_PASS`/`REVIEW_PASS`, the deferred-observations prose spelling, or the `Spec:`/`Governing spec:` tags.

### Phase 2: Verify

- [x] **Task 4: Run the spec's verification greps** (depends on Tasks 1–3)
  Files: none (verification only)
  From the repo root run `grep -rniE "\bmilestone" orchestrator/prompts/*.md` → expect zero hits. Run `grep -n '## Deferred observations\|- Affects:\|PLAN_REVIEW_PASS\|REVIEW_PASS' orchestrator/prompts/reviewer.md` → confirm those tokens are present and unchanged. Confirm `git diff` touches only `planner.md`, `test-planner.md`, `reviewer.md` (no `implementer.md`, no other file). If any grep fails, return to the relevant task above.
