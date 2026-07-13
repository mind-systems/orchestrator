# Remove the vestigial Commit Plan instruction from the planner prompt

**Date:** 2026-07-13
**Source:** conversation context

## Problem today

The planner prompt tells the planner to author a multi-commit plan:

- `orchestrator/prompts/planner.md:111–117` — `**Commit Plan** — add when there are 5+ tasks:` plus a fenced `## Commit Plan` example (`Commit 1` after tasks 1-3, `Commit 2` after tasks 4-6).
- `orchestrator/prompts/planner.md:119–123` — `**Commit Plan Rules:**` (checkpoints every 3–5 tasks, group logically, `NO conventional commit prefixes`).
- `orchestrator/prompts/planner.md:142` — Important Rule #7, `**Commit checkpoints for large plans**`.
- `orchestrator/prompts/implementer.md:32` — `- Commit checkpoints (when to commit — note: the orchestrator handles actual commits)`.

But nothing executes this plan. The implementer is told commits are not its job, and the orchestrator commits **exactly once per completed task**: `_git_commit` (`main.py:177`) runs `git add -A` and a single `git commit`, with the message built from the task title alone —

```python
message = f"{milestone_title}\n\nCo-Authored-By: AI Orchestrator <noreply@orchestrator>"
```

(`milestone_title` is the current parameter name; Phase 5 renames it — do not depend on the name here.)

So the carefully-authored `## Commit Plan` never materializes: every task collapses into one commit regardless of the checkpoints. The artifact is not merely dead — it **contradicts the model**: a task is the atomic unit of revert (one reason to revert), and a genuinely separable commit would be a separate task, not an in-plan checkpoint. The `NO conventional commit prefixes` line is likewise moot — the commit message is the task title, authored at the roadmap layer, never derived from the plan.

## The change

Prompt-only edits, two files:

- **`planner.md`** — delete the `**Commit Plan**` heading, the fenced `## Commit Plan` example, and the `**Commit Plan Rules:**` block (the run of lines 111–123). Delete Important Rule #7 (`Commit checkpoints for large plans`, line 142) and renumber the rules after it so the list stays contiguous (`8 → 7`, `9 → 8`).
- **`implementer.md:32`** — replace the `Commit checkpoints …` bullet with a one-liner stating commits are the orchestrator's concern (e.g. `- Commits are handled by the orchestrator — do not run git yourself`).

Everything else in the Plan file format (the `## Tasks` / `### Phase` structure) stays intact.

## Verify

- `grep -rn 'Commit Plan\|commit checkpoint\|checkpoint' orchestrator/prompts/` → no hits.
- `planner.md` still carries its `## Tasks` format section, and its Important Rules are numbered contiguously `1..N`.
- `git diff --stat` touches only `orchestrator/prompts/planner.md` and `orchestrator/prompts/implementer.md` — no code file changed.

## What NOT to do

- Do **not** touch `_git_commit` or any commit/push code — one-commit-per-task is already the intended behavior; this is a prompt cleanup, not a behavior change.
- Do **not** conform `milestone → task` or any other vocabulary in these prompts here — that is Phase 7's scope. Touch only the commit-plan lines.
- Do **not** remove the rest of the planner's Plan file format or the other Important Rules — only the Commit Plan pieces and rule #7.

## Tests

None. The prompts are static data (a loud-failure surface — a broken prompt shows up immediately in a run, not as a silent wrong result), so there is nothing to unit-test; verification is the `grep` and `git diff --stat` above.
