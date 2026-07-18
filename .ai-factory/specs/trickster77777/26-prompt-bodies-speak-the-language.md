# Prompt bodies speak the language

**Date:** 2026-07-14
**Source:** conversation context — editor decomposition of Phase 7, ratified by the architect; revised after the architect reconsidered introducing a second word for the plan's checklist item — a plan's own "task" reads consistently in its own scope, exactly like `phase` already reads consistently across a roadmap and a plan (`using-the-language.md` § "The one rule"), so no rename was needed there; amended 2026-07-18 per [handoff 07](../../handoffs/07-language-contract-softened-to-naming-only.md) — the contract is naming-only, so every hyphenation clause is dropped and the `task-spec` targets become plain `task spec`

## Problem today

Three of the four agent prompts (`orchestrator/prompts/planner.md`, `test-planner.md`, `reviewer.md`) still name the roadmap unit with the retired word "milestone" — the thing the pipeline plans, reviews, and marks done. `reserved-words.md` § Roadmap artifacts fixes the canonical form as `task`. These prompts shape every plan and review the orchestrator writes, so this is the surface that makes the produced artifacts, and the agents reading these instructions, speak the language going forward. The prompts also use the synonym "full specification" where the vocabulary names the concept `task spec` — the one other word-choice fix here. Their existing spellings of the other reserved terms ("named roadmap", "deferred observation(s)") are ordinary English and already conformant: the contract binds word choice, never typography, so no spelling is swept.

The plan's own checklist items (`## Tasks`, `**Task N: <subject>**`) are untouched: "task" there names a unit of work inside a plan, reading exactly the same way "phase" already reads consistently in both a roadmap phase and a plan phase — one word, one meaning, applied at two altitudes of the same structure, not a collision. The plan format and every plan-checklist "task" stay exactly as they are today.

This is prose-only. No code, no runtime message, no artifact-format byte change — the prompts are read by the LLM agents at session start, not parsed by the orchestrator, so nothing here is a protocol change (contrast Phase 6's breaking token rename).

## The change

Two slices, both confined to three prompt files' prose (not their protocol literals — see Guards). `implementer.md` has no change under this task — it never named the roadmap unit "milestone", and its plan-checklist "task" wording is left alone like every other prompt's.

### 1. Roadmap unit: `milestone` → `task`

**`planner.md`:**

| Line | Current | New |
|---|---|---|
| 3 | "single milestone" | "single task" |
| 5 | "milestone title" | "task title" |
| 21 | "The milestone line and everything it references form the context tree for this task" | "The task line and everything it references form the context tree for this task" |
| 22 | "Read the note behind the milestone's `Spec:` tag — it is the full specification; the line is its header." | "Read the note behind the task's `Spec:` tag — the full task spec; the line is its header." |
| 24 | "Reading your milestone's line in the roadmap, check its phase header" | "Reading your task's line in the roadmap, check its phase header" |
| 25 | "Follow only links reachable from your milestone" | "Follow only links reachable from your task" |
| 48 | "From the milestone description, identify:" | "From the task description, identify:" |
| 82 | "# Plan: <milestone title>" | "# Plan: <task title>" |
| 85 | "<1-2 sentences: what this milestone achieves>" | "<1-2 sentences: what this task achieves>" |
| 136 | "Don't add test tasks unless the milestone explicitly requires them" | "Don't add test tasks unless the task explicitly requires them" — only `milestone` renames; "test tasks" is the plan-checklist meaning and stays untouched |
| 143 | "only what the milestone description asks for" | "only what the task description asks for" |

**`test-planner.md`:**

| Line | Current | New |
|---|---|---|
| 3 | "writing a test plan for a specific milestone. The milestone already tells you what to test" | "writing a test plan for a specific task. The task already tells you what to test" |
| 5 | "milestone title" | "task title" |
| 18 | "The milestone line and everything it references form the context tree for this task" | "The task line and everything it references form the context tree for this task" |
| 19 | "Read the note behind the milestone's `Spec:` tag — it is the full specification; the line is its header." | "Read the note behind the task's `Spec:` tag — the full task spec; the line is its header." |
| 21 | "Reading your milestone's line in the roadmap, check its phase header" | "Reading your task's line in the roadmap, check its phase header" |
| 22 | "Follow only links reachable from your milestone" | "Follow only links reachable from your task" |
| 27 | "### Step 1: Read the Milestone" | "### Step 1: Read the Task" |
| 29 | "Extract from the milestone description:" | "Extract from the task description:" |
| 38 | "Read each source file that the milestone asks to test **in full**." | "Read each source file that the task asks to test **in full**." |
| 76 | "# Test Plan: <milestone title>" | "# Test Plan: <task title>" |
| 125 | "Only test what the milestone specifies" | "Only test what the task specifies" |

**`reviewer.md`:**

| Line | Current | New |
|---|---|---|
| 23 | "a named roadmap under `.ai-factory/roadmaps/` (if present) — for milestone alignment" | "a named roadmap under `.ai-factory/roadmaps/` (if present) — for task alignment" ("named roadmap" is already the registry name in plain English — only `milestone` renames) |
| 24 | "Follow mentions from the milestone under review" | "Follow mentions from the task under review" |
| 25 | "match the plan's `# Plan: <milestone title>` heading … to find the milestone's line" | "match the plan's `# Plan: <task title>` heading … to find the task's line" |
| 112 | "outside the current milestone's scope … or a file boundary this milestone does not touch" | "outside the current task's scope … or a file boundary this task does not touch" |
| 113 | "fixable within the milestone's boundary" | "fixable within the task's boundary" |
| 114 | "without leaving the milestone's file boundary" | "without leaving the task's file boundary" |
| 116 | "If an earlier review file for this milestone already carries such marks" | "If an earlier review file for this task already carries such marks" |

### 2. Synonym alignment

One synonym retires: "the full specification" → "the full task spec" at `planner.md:22` and `test-planner.md:19` (folded into slice 1's table rows above). Nothing else in the prompts' prose changes spelling: "named roadmap" (`reviewer.md:23`) and every "deferred observation(s)" phrase around the review-channel paragraph (`reviewer.md:111–120`) are already the registry names written in ordinary English — the contract binds word choice, not typography, and no text is swept for hyphens or capitals. "No change" is the outcome for those lines.

## Guards

- **Protocol literals stay legacy (cross-repo shared surface).** The `## Deferred observations` heading and the `- Affects: <phase / spec-note path / "unknown">` entry line (`reviewer.md` lines 106, 108), the `PLAN_REVIEW_PASS` / `REVIEW_PASS` literals (`reviewer.md` lines 118–121), and the `Spec:` / `Governing spec:` tags (`planner.md:22,24`; `test-planner.md:19,21`; `reviewer.md:24`) are mechanism, not vocabulary — a program scans or emits these exact bytes. They stay byte-for-byte unchanged. This is a joint contract with the skills side, already pinned there in spec 62; the rule itself is in `skills/docs/using-the-language.md` § "Protocol tokens are a different axis" ("protocol tokens are mechanism, not vocabulary, byte-for-byte"), and the coordination is recorded in `skills/.ai-factory/handoffs/21-review-file-protocol-is-shared-conform-in-lockstep.md`. No later task on either side reopens this — a token the orchestrator emits and a skill scans changes in lockstep or not at all.
- Do not touch any code file, runtime message, or config — this task's surface is the three prompt files' prose only.
- Do not touch `implementer.md` — it has no "milestone" occurrence and its plan-checklist "task" wording is out of scope (not a collision; see Problem today).

## Verify

- `grep -rniE "\bmilestone" orchestrator/prompts/*.md` → zero hits.
- A manual pass over the three touched files confirming every remaining `task`/`Task` — including every plan-checklist `## Tasks` / `**Task N:**` occurrence — is untouched or, where it named the roadmap unit, now reads `task`.
- `grep -n '## Deferred observations\|- Affects:\|PLAN_REVIEW_PASS\|REVIEW_PASS' orchestrator/prompts/reviewer.md` shows these tokens unchanged (byte-for-byte) from before this task ran.
- `git diff` touches only `orchestrator/prompts/planner.md`, `test-planner.md`, `reviewer.md` — no other file in the diff, `implementer.md` included.

## What NOT to do

- Do not touch `## Tasks`, `**Task N: <subject>**`, `# Plan: <task title>`'s checklist, or any other plan-format/plan-checklist wording — the plan structure is unchanged by this task.
- Do not touch `implementer.md` at all.
- Do not touch the `## Deferred observations` heading, the `- Affects:` entry line, `PLAN_REVIEW_PASS`/`REVIEW_PASS`, or any `Spec:`/`Governing spec:` tag — protocol literals, byte-for-byte.
- Do not touch any `.py` file, `docs/*.md`, `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, or config — out of this task's scope (Phases 5, 6, 8 respectively).
- Do not sweep typography — no hyphenation or capitalization pass anywhere: "named roadmap", "deferred observation(s)", and every other reserved term keep their existing ordinary-English spelling.
- Do not invent a `PASS-signal` prose rename — no such generic wording exists in these files outside the literal `PLAN_REVIEW_PASS`/`REVIEW_PASS` tokens themselves, which stay untouched.

## Tests

None. The prompt files are static text read by an LLM agent at session start — a loud-failure surface with no parser to break silently (contrast the code/config renames in Phases 5–6, which do have `pytest` coverage). Correctness here is verified by the greps above, not a test run.
