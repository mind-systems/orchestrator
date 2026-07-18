# Review: 9.1 — Drop the vestigial Commit Plan instruction

## Scope
Prompt-only cleanup across two files. Verified `git diff HEAD` and `git status`; read both changed files in full.

## Changes reviewed

### `orchestrator/prompts/planner.md`
- Removed the `**Commit Plan**` heading, the fenced `## Commit Plan` example, and the `**Commit Plan Rules:**` block (former lines 111–123). The `---` separator and the following `## Task Description Requirements` section are intact.
- Deleted Important Rule #7 (`Commit checkpoints for large plans`) and renumbered the tail: `No gold-plating` → 7, `All output must be in English` → 8. The `## Important Rules` list is contiguous `1..8` with no gaps or duplicates.

### `orchestrator/prompts/implementer.md`
- Line 32 replaced: the `Commit checkpoints (when to commit …)` bullet is now `- Commits are handled by the orchestrator — do not run git yourself`. Surrounding bullets (Context and settings, Task dependencies) untouched.

## Verification
- `grep -rn 'Commit Plan\|commit checkpoint\|checkpoint' orchestrator/prompts/` → no hits (exit 1).
- `planner.md` retains its `## Tasks` format section and `## Task Description Requirements`; Important Rules numbered contiguously `1..8`.
- `git diff HEAD --stat` touches only `orchestrator/prompts/planner.md` and `orchestrator/prompts/implementer.md` — no code file changed, `_git_commit` untouched.
- No `milestone → task` vocabulary changes introduced (correctly out of scope).

## Correctness / runtime
Prompts are static data read at runtime by the agents; there are no types, migrations, or concurrency surfaces. The removed instruction was never executed (`_git_commit` in `main.py:177` makes one commit per task), so removal is behavior-preserving for the pipeline and removes a contradiction the planner would otherwise author. The implementer's new one-liner aligns with the existing "orchestrator handles actual commits" intent.

No findings.

REVIEW_PASS
