# Plan: Prompts: follow mentions from the contract line

## Context
Add a single "follow mentions" rule to the planner and reviewer prompts so agents lift the full context tree (the `Spec:` note, what it references, and any `Governing spec:` in the phase header) from the milestone's own contract line — instead of relying on the fixed `DESCRIPTION`/`ARCHITECTURE`/`RULES`/`ROADMAP` checklists that let the governing spec go unread. Prompt files only; no Python changes.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Prompt edits

- [x] **Task 1: Add follow-mentions block to `planner.md` Step 0**
  Files: `orchestrator/prompts/planner.md`
  In `### Step 0: Load Project Context`, after the existing `**ALSO:** Read .ai-factory/RULES.md` bullet block (ends at line 25, before the `---` at line 33), append one new block in the file's existing bold-lead-in + bullets style. Lead-in: `**Follow mentions.**` with the framing "The milestone line and everything it references form the context tree for this task:". Bullets, verbatim from the spec:
  - Read the note behind the milestone's `Spec:` tag — it is the full specification; the line is its header.
  - Read what that note itself mentions (other notes, docs) where it concerns the surface being planned.
  - Reading your milestone's line in the roadmap, check its phase header — if it names `Governing spec:` documents, read them.
  - Follow only links reachable from your milestone; do not sweep the notes directory or read specs of unrelated tasks.
  Do NOT alter the existing DESCRIPTION/ARCHITECTURE/RULES bullets, the "Use this context when" list, or any other step. No authority/ordering language. Source: `.ai-factory/notes/03-follow-mentions.md` Edit 1.

- [x] **Task 2: Mirror the follow-mentions block into `test-planner.md` Step 0**
  Files: `orchestrator/prompts/test-planner.md`
  In `### Step 0: Load Project Context`, after the existing `**Read .ai-factory/RULES.md**` block (ends at line 20, before the `---` at line 22), append the same `**Follow mentions.**` block described in Task 1, matching `test-planner.md`'s own register. Keep the four bullets identical in intent to Task 1. Do not touch Steps 1–4 or the test-specific structure. Source: note Edit 1 ("mirrored in `test-planner.md` Step 0").

- [x] **Task 3: Add the follow-mentions gate to `reviewer.md` Context Gates**
  Files: `orchestrator/prompts/reviewer.md`
  In `## Context Gates (Read-Only)`, alongside the existing ARCHITECTURE/RULES/ROADMAP bullets (lines 16-18), add one new gate in the same bullet style, consisting of two points:
  - Follow mentions from the milestone under review: the `Spec:` note behind its tag, what that note references, and any `Governing spec:` named by its phase — findings are judged against this tree, not against the roadmap line alone.
  - When the session holds only a plan path (plan review), first recover the root: match the plan's `# Plan: <milestone title>` heading against `.ai-factory/ROADMAP.md` — or `.ai-factory/ROADMAP_TESTS.md` when reviewing a test plan — to find the milestone's line. If no line matches, skip this gate.
  Keep the existing WARN/ERROR severity note and every other section intact. No authority language; graceful no-op when there are no mentions. Source: note Edit 2.

## Notes
- All three edits are additive and a few lines each — no rewrites, no removed content.
- Do NOT touch `implementer.md`, `agents.py`, `main.py`, `roadmap.py`, or any plumbing.
- Single commit after all three tasks: "Add follow-mentions rule to planner, test-planner, and reviewer prompts".
