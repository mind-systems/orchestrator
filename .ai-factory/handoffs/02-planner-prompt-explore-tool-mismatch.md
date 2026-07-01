# Handoff — planner-prompt-explore-tool-mismatch

## 1. Frame
The planner prompt instructs the agent to spawn Explore sub-agents via the `Task` tool, but the orchestrator never grants that tool to the planner session — the instructions are dead weight, saved by a fallback. This note is a self-contained bug report so a fresh agent in this repo can decide the fix; it was surfaced from outside (during an ai-factory skills sync) and is durable in the files cited below, not in any live chat.

## 2. Read-first map

### Must-read now (minimal rehydration set)
- `orchestrator/prompts/planner.md` — Step 1 ("Quick Reconnaissance") and Step 3 ("Explore Codebase") instruct `Task(subagent_type: Explore, ...)` and "Launch 2-3 Explore agents simultaneously".
- `orchestrator/agents.py:249` — `self.tools = ["Read", "Write", "Glob", "Grep", "Bash"]` — the exact toolset the planner session runs with. No `Task`, no Explore. Same list for the standalone reviewer at `agents.py:323`. Both pass `allowed_tools=self.tools` into `_run_claude` (the `claude` CLI with `--allowedTools`).

### Read on demand
- `~/projects/skills/src/skills/aif-plan/SKILL.md` + `.../references/EXAMPLES.md` — the sibling skill this prompt was cloned from. Its `EXAMPLES.md` had the same class of staleness (described fast/full/parallel modes + branches/worktrees the rewritten SKILL.md no longer does) and was already fixed in that repo. `planner.md` inherited the interactive-Claude-Code assumption (Explore/Task available) into this headless context.

## 3. Current state

**Done:**
- Diagnosed: `planner.md` Steps 1 & 3 instruct Explore/Task sub-agents the planner cannot use.
- Confirmed toolset: `agents.py:249` (planner+reviewer session) and `agents.py:323` (standalone reviewer) both grant only `["Read", "Write", "Glob", "Grep", "Bash"]`.
- Scoped the blast radius: `grep -rlnE 'subagent_type:\s*Explore|Task\(subagent' orchestrator/prompts/` matches **only `planner.md`**. `test-planner.md`, `reviewer.md`, `implementer.md` are clean — do not touch them for this.

**In-flight:**
- The fix itself. Deliberately NOT applied — the owner wanted a report, and the fix direction is a judgment call (see Next step).

**Uncommitted working-tree state:**
- none in this repo (read-only investigation here; the paired `EXAMPLES.md` fix landed in `~/projects/skills`, a different repo).

## 4. Next step
Pick a direction and apply it to `planner.md` only:
- **(a) Match the real toolset (smaller, safer):** rewrite Step 1 and Step 3 to do direct `Glob`/`Grep`/`Read` exploration; delete the "Launch 2-3 Explore agents" block and the `Agent 1/2/3` `Task(...)` templates and the "Fallback: If Task tool is unavailable" line (which only exists to paper over this). Removes ~30 lines the planner loads and reasons around every run.
- **(b) Grant the tool (bigger):** add `Task`/Agent to `self.tools` in `agents.py` if sub-agent exploration is genuinely wanted — but first verify the headless `claude` CLI invocation in `agents.py` (`_run_claude`, `--dangerously-skip-permissions --allowedTools ...`) actually supports spawning sub-agents in this runtime. If unverified, prefer (a).

## 5. Working discipline
- Report-only was the explicit instruction that produced this note: diagnose, don't fix — the owner decides. Carry that forward: propose the direction, get a nod before editing prompts or `agents.py`.
- No commits without explicit permission.

## 6. Error log
- Initial guess "test-planner.md likely shares the pattern" was **wrong** — a grep proved only `planner.md` contains the Explore/Task instructions. Verify with grep before touching sibling prompts; do not fix `test-planner.md`/`reviewer.md`/`implementer.md` on assumption.

## 7. Orientation
- **The fallback masks the bug.** `planner.md` ends Step 3 with "Fallback: If Task tool is unavailable, use Glob/Grep/Read directly", so runs never break — the cost is silent (dead prompt weight; worst case one wasted turn: attempt `Task` → tool error → fall back). "It works" is not evidence the instructions are correct.
- **Don't over-fix.** These parts of `planner.md` are correct and must stay: the plan path is passed in externally (Step 4, "the exact path is already determined and passed to you"); the plan-file format is self-contained (no dependency on the skill's `TASK-FORMAT.md`); the Commit Plan rules explicitly ban conventional-commit prefixes; `## Settings` is hardcoded (`Testing: no / Logging: minimal / Docs: no`) on purpose because the planner is non-interactive.
