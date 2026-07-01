# Planner Step 3 — replace dead Explore/Task sub-agents with direct Glob/Grep/Read

**Date:** 2026-07-01
**Source:** conversation context

## Key Findings

- `orchestrator/prompts/planner.md` Step 3 ("Explore Codebase") instructs the planner to launch 2-3 `Task(subagent_type: Explore)` sub-agents, but the planner session never gets the `Task` tool — its toolset is `["Read", "Write", "Glob", "Grep", "Bash"]` (`agents.py:249`). The primary path of Step 3 is dead code; every run silently takes the `Fallback: If Task tool is unavailable` branch.
- This is a **half-finished fork** of `/aif-plan`, not a general bug. Step 1 ("Quick Reconnaissance") in the *same file* was already correctly converted to direct `Glob/Grep/Read`; Step 3 was copied verbatim from the interactive skill and never converted. The file contradicts itself (Step 1 = Glob/Grep, Step 3 = Task/Explore).
- Scope confirmed by grep `subagent_type:\s*Explore|Task\(subagent` over `orchestrator/prompts/`: **only `planner.md` matches**. `test-planner.md`, `reviewer.md`, `implementer.md` are clean.
- Chosen direction: **(a2)** — convert Step 3 to direct exploration in place, keep the synthesis bullets. Rejected: **(b)** granting `Task` in `agents.py` (unverified whether the headless `claude` CLI supports sub-agent spawning; no clear benefit).

## Details

### Current state (planner.md, ~lines 55-87)
Step 3 contains:
- A prose line: "understand the existing code through **parallel exploration**."
- A fenced block with three `Agent 1/2/3 — …: Task(subagent_type: Explore, model: sonnet, prompt: "…")` templates.
- "Use recon from Step 1 as a starting point."
- An "**After agents return, synthesize:**" bullet list (which files to create/modify, patterns to follow, dependencies, risks).
- "**Fallback:** If Task tool is unavailable, use Glob/Grep/Read directly."

### The change
- Remove the three `Task(subagent_type: Explore …)` templates and the "parallel exploration" / "Launch 2-3 Explore agents" framing.
- Remove the "Fallback:" line (it only exists to paper over the missing tool).
- Reframe Step 3 as: drill deeper with `Glob`/`Grep`/`Read` into the areas Step 1 recon flagged as needing more understanding (architecture & affected modules, existing patterns/conventions, dependencies & integration points).
- **Keep** the "synthesize" bullets — reword the header from "After agents return, synthesize" to synthesis after direct exploration. These bullets (files to create/modify, patterns, dependencies, risks) are the real value of the step and must survive.
- Net effect: ~30 lines removed; Step 3 becomes consistent with Step 1.

### Guards
- Touch **`orchestrator/prompts/planner.md` only**. Do NOT modify `agents.py` (that is direction b, rejected).
- Do NOT touch `test-planner.md`, `reviewer.md`, `implementer.md` — grep proved they lack this pattern.
- Do NOT alter these correct, deliberately-headless parts of `planner.md`: Step 4's externally-passed plan path ("the exact path is already determined and passed to you"); the self-contained plan-file format; the `## Settings` hardcode (Testing: no / Logging: minimal / Docs: no); the conventional-commit-prefix ban; the "output only `done`" final rule.

### Verify
- `grep -rnE 'subagent_type:\s*Explore|Task\(subagent|Fallback: If Task' orchestrator/prompts/` returns nothing.
- Both Step 1 and Step 3 of `planner.md` reference only `Glob`/`Grep`/`Read`.
- The synthesis bullets (files, patterns, dependencies, risks) are still present in Step 3.

## Open Questions

- None blocking. If sub-agent exploration is ever genuinely wanted, direction (b) can be revisited — but only after verifying the headless `claude` CLI in `_run_claude` actually supports spawning `Task`/Explore sub-agents.
