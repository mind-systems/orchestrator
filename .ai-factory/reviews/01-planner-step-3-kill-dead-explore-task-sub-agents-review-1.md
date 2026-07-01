# Code Review: Planner Step 3 — kill dead Explore/Task sub-agents

## Scope
Single-file prompt change: `orchestrator/prompts/planner.md`, Step 3 ("Explore Codebase"). Reviewed `git diff HEAD` and `git status`; the only code/prompt file changed is `planner.md` (the other staged items are planning artifacts under `.ai-factory/`).

## Verification against the plan
- **Dead primary path removed:** the fenced block with the three `Task(subagent_type: Explore, model: sonnet, ...)` templates (Agent 1/2/3) is deleted.
- **Fallback line removed:** `**Fallback:** If Task tool is unavailable, use Glob/Grep/Read directly.` is gone.
- **Reframed to direct exploration:** Step 3 now drills deeper with `Glob`/`Grep`/`Read`, keeps "Use recon from Step 1 as a starting point", and preserves the same three angles as bullets (architecture & affected modules, existing patterns & conventions, dependencies & integration points).
- **Synthesis bullets kept:** files to create/modify, patterns to follow, dependencies, risks — all present under the reworded header "After direct exploration, synthesize:".
- **Consistency:** Step 1 and Step 3 both now reference only `Glob`/`Grep`/`Read`; the self-contradiction is resolved.
- **Guards respected:** Step 0/1/2/4 and everything after Step 4 are unchanged (confirmed by full-file read); externally-passed plan path wording, `## Settings` hardcode, conventional-commit-prefix ban, and the "output only `done`" final rule are intact. `agents.py`, `test-planner.md`, `reviewer.md`, `implementer.md` untouched.

## Automated checks
- `grep -rnE 'subagent_type:\s*Explore|Task\(subagent|Fallback: If Task' orchestrator/prompts/` → no matches (exit 1). Confirms no dead references remain.

## Runtime / correctness assessment
This is a prompt documentation change with no executable code, types, migrations, or concurrency concerns. Nothing breaks at runtime; the edit removes instructions that referenced a `Task` tool the planner session never has (`agents.py:249` toolset is `["Read","Write","Glob","Grep","Bash"]`), which strictly reduces confusion. No bugs, security issues, or correctness problems found.

REVIEW_PASS
