# Plan: Planner Step 3 — kill dead Explore/Task sub-agents

## Context
Step 3 of `orchestrator/prompts/planner.md` instructs the planner to launch `Task(subagent_type: Explore)` sub-agents, but the planner session lacks the `Task` tool (`agents.py:249` grants only `["Read","Write","Glob","Grep","Bash"]`), so the primary path is dead code and every run silently falls through to the fallback branch. This milestone rewrites Step 3 to use direct `Glob/Grep/Read` exploration, consistent with Step 1.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Rewrite Step 3

- [x] **Task 1: Convert Step 3 "Explore Codebase" to direct Glob/Grep/Read exploration**
  Files: `orchestrator/prompts/planner.md`
  Rewrite only the Step 3 section (currently ~lines 55–87). Specifically:
  - Remove the "understand the existing code through **parallel exploration**" framing and the "Launch 2-3 Explore agents simultaneously" line.
  - Delete the fenced code block containing the three `Task(subagent_type: Explore, model: sonnet, prompt: ...)` templates (Agent 1 / Agent 2 / Agent 3).
  - Delete the "**Fallback:** If Task tool is unavailable, use Glob/Grep/Read directly." line.
  - Reframe the step as: drill deeper with `Glob`/`Grep`/`Read` into the areas Step 1 recon flagged, covering the same three angles — (1) architecture & affected modules, (2) existing patterns & conventions, (3) dependencies & integration points. Keep "Use recon from Step 1 as a starting point" phrasing.
  - **Keep** the synthesis bullets (which files to create/modify, what patterns to follow, dependencies between components, potential risks/edge cases). Reword the header from "**After agents return, synthesize:**" to reflect synthesis after direct exploration.
  - Do NOT touch Step 0, Step 1, Step 2, Step 4, or any section after Step 4. Leave the externally-passed plan path wording, the `## Settings` hardcode (Testing: no / Logging: minimal / Docs: no), the conventional-commit-prefix ban, and the "output only `done`" final rule intact.
  - Do NOT modify `agents.py`, `test-planner.md`, `reviewer.md`, or `implementer.md`.

- [x] **Task 2: Verify the rewrite** (depends on Task 1)
  Files: `orchestrator/prompts/planner.md`
  Confirm the change is correct and self-consistent:
  - `grep -rnE 'subagent_type:\s*Explore|Task\(subagent|Fallback: If Task' orchestrator/prompts/` returns nothing.
  - Both Step 1 and Step 3 of `planner.md` reference only `Glob`/`Grep`/`Read`.
  - The synthesis bullets (files, patterns, dependencies, risks) are still present in Step 3.
