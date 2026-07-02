# Prompts: follow mentions from the contract line

**Date:** 2026-07-02
**Source:** conversation context (context-breadth analysis + tradeoxy Phase 7 incident)

## Key Findings

- No prompt follows references. Both agent prompts carry fixed checklists instead: `planner.md` Step 0 reads `DESCRIPTION.md` / `ARCHITECTURE.md` / `RULES.md`; `reviewer.md` Context Gates read `ARCHITECTURE.md` / `RULES.md` / `ROADMAP.md` ("for milestone alignment"). Nothing instructs going from the milestone's own line out along its links — the `Spec:` note is read only opportunistically, because its path happens to sit in the description text the agent receives.
- Live incident (tradeoxy Phase 7): three code-review rounds in a row issued semantic blockers without ever opening the governing spec named in the milestone's phase header — the ratified spec tier did not participate in review at all.
- The fix is **one rule, not a list of special documents**: lift the context tree from your own contract line — **follow mentions**. The `Spec:` tag is a mention; whatever the note mentions (other notes, docs) are next-level mentions; a `Governing spec:` line in the phase header is a mention too, visible when reading your milestone's line in the roadmap. Depth limiting is built into the rule itself: only links reachable from your task are followed — the lazy per-task tree (`docs/context-model.md`), never "read all the notes".
- In plan review the tree has no root edge: `PlanReviewer.review_plan()` (`agents.py:327`) runs a fresh session and passes only the plan path — no milestone title, no roadmap path/line. The only way back to the contract line is the plan's `# Plan: <milestone title>` heading matched against the roadmap; in test mode the line lives in `ROADMAP_TESTS.md`, which the existing gates never name. (Code review is unaffected: it runs in the planner's session, which received the milestone and roadmap line literally.)

## Details

### Edit 1 — `planner.md` Step 0 (mirrored in `test-planner.md` Step 0)

Both files share the `### Step 0: Load Project Context` structure ending with the `RULES.md` block. Append one block after it, in the file's existing style (bold lead-in + bullets):

**Follow mentions.** The milestone line and everything it references form the context tree for this task:
- Read the note behind the milestone's `Spec:` tag — it is the full specification; the line is its header.
- Read what that note itself mentions (other notes, docs) where it concerns the surface being planned.
- Reading your milestone's line in the roadmap, check its phase header — if it names `Governing spec:` documents, read them.
- Follow only links reachable from your milestone; do not sweep the notes directory or read specs of unrelated tasks.

### Edit 2 — `reviewer.md` Context Gates

Add one gate alongside the existing `ARCHITECTURE.md` / `RULES.md` / `ROADMAP.md` checks, same style as its neighbors:

- Follow mentions from the milestone under review: the `Spec:` note behind its tag, what that note references, and any `Governing spec:` named by its phase — findings are judged against this tree, not against the roadmap line alone.
- When the session holds only a plan path (plan review), first recover the root: match the plan's `# Plan: <milestone title>` heading against `.ai-factory/ROADMAP.md` — or `.ai-factory/ROADMAP_TESTS.md` when reviewing a test plan — to find the milestone's line. If no line matches, skip this gate.

### Constraints

- Prompt files only — no changes to `agents.py`, `main.py`, `roadmap.py`, or the prompt-passing plumbing.
- A few lines per file, matching each file's existing register.
- Graceful no-op when there are no mentions to follow (plain single-tier roadmaps: no `Spec:` tags, no `Governing spec:` — checklist behavior unchanged).

## What NOT to do

- Do not make the agents read the whole notes directory or all specs "to be safe" — the rule is follow-links-from-your-line, which self-limits depth; eager sweeps are the failure mode this rule avoids.
- Do not add authority language (ratified / do-not-re-decide / must-cite-not-re-litigate) — tier authority is a separate topic, out of this task's scope.
- Do not impose reading order or "in full, first" pressure beyond following the links.
- Do not add a new prompt file or a config flag.
- Do not touch `implementer.md` — the implementer works from the plan, which the planner (now tree-fed) produces.
