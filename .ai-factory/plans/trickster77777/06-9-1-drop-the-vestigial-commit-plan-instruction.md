# Plan: 9.1 — Drop the vestigial Commit Plan instruction

## Context
Remove the multi-commit `## Commit Plan` instruction from the planner prompt and reduce the implementer's "commit checkpoints" bullet to a one-liner, so the prompts describe only what the orchestrator actually runs (one commit per completed task).

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Prompt cleanup

- [x] **Task 1: Remove the Commit Plan block and rule #7 from `planner.md`**
  Files: `orchestrator/prompts/planner.md`
  Delete the run of lines 111–123 in full: the `**Commit Plan** — add when there are 5+ tasks:` heading, the fenced ```markdown ... ## Commit Plan ...``` example (Commit 1 after tasks 1-3, Commit 2 after tasks 4-6), and the `**Commit Plan Rules:**` bullet block. Leave the `---` separator (line 125) and the `## Task Description Requirements` section that follows intact. In the `## Important Rules` list, delete rule `7. **Commit checkpoints for large plans** …` and renumber the remaining rules so they stay contiguous `1..N`: current `8. **No gold-plating** …` becomes `7`, current `9. **All output must be in English**` becomes `8`. Do not touch rules 1–6, the `## Tasks` / `### Phase` plan format, or any other content. Do not conform `milestone → task` vocabulary (out of scope — Phase 7).

- [x] **Task 2: Reduce the implementer's commit-checkpoints bullet to a one-liner**
  Files: `orchestrator/prompts/implementer.md`
  Replace line 32, `- Commit checkpoints (when to commit — note: the orchestrator handles actual commits)`, with a one-liner stating commits are the orchestrator's concern — e.g. `- Commits are handled by the orchestrator — do not run git yourself`. Leave the surrounding `### Step 1: Read the Plan` bullets (Context and settings, Task dependencies) intact.

## Verification (manual, no tests)
- `grep -rn 'Commit Plan\|commit checkpoint\|checkpoint' orchestrator/prompts/` → no hits.
- `planner.md` still carries its `## Tasks` format section and `## Task Description Requirements`; its Important Rules are numbered contiguously `1..8`.
- `git diff --stat` touches only `orchestrator/prompts/planner.md` and `orchestrator/prompts/implementer.md` — no code file changed.
