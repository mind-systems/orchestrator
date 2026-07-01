# Plan Review: Planner Step 3 — kill dead Explore/Task sub-agents

## Code Review Summary

**Files Reviewed:** 1 plan targeting 1 source file (`orchestrator/prompts/planner.md`)
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): No boundary/dependency concerns. The change is a prompt-only edit to `planner.md`; it introduces no new module coupling and touches no code paths. WARN: none.
- **Rules** (`.ai-factory/RULES.md`): absent — WARN (optional file, no rules to enforce).
- **Roadmap** (`.ai-factory/ROADMAP.md` present): Milestone linkage confirmed. ROADMAP.md line 11 describes this exact milestone, including the same `agents.py:249` toolset evidence and the same scoping constraints (touch `planner.md` only). The plan faithfully reflects the roadmap entry. No missing linkage.
- **Skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`): absent — no project-specific review overrides to apply.

### Verified Assumptions (all correct)
- `agents.py:249` grants `["Read", "Write", "Glob", "Grep", "Bash"]` with no `Task` tool — **confirmed**. The primary Explore path is genuinely dead code.
- Step 3 currently spans lines 55–87 as stated — **confirmed**.
- The three `Task(subagent_type: Explore, ...)` templates (lines 61–77) and the `Fallback: If Task tool is unavailable` line (87) exist as described — **confirmed**.
- Step 1 (line 37) already uses direct `Glob/Grep/Read`, so the rewrite is consistent with an existing in-file pattern — **confirmed**.
- The synthesis bullets (lines 81–85: files to create/modify, patterns, dependencies, risks) exist and the plan preserves them — **confirmed**.
- `planner.md` is the **only** prompt containing the `Task(subagent_type: Explore)` / `Fallback` pattern — verified across `orchestrator/prompts/*.md`. Scoping the change to `planner.md` alone leaves no sibling file with the same dead code, so the "do NOT modify test-planner.md/reviewer.md/implementer.md" constraint is safe and complete.

### Critical Issues
None.

### Observations (non-blocking)
- **Task 2 verification is well-formed.** The `grep -rnE 'subagent_type:\s*Explore|Task\(subagent|Fallback: If Task' orchestrator/prompts/` command currently matches lines 63/68/74 and will correctly return empty once Task 1 lands. Good, executable acceptance criterion.
- **Line-range drift is handled.** The plan says "currently ~lines 55–87" (with a tilde) and anchors edits by content (specific headers, the fenced block, the Fallback line) rather than by hard line numbers — resilient to minor shifts. No action needed.
- The plan explicitly enumerates what must stay intact (Steps 0/1/2/4, the externally-passed plan path wording, the `## Settings` hardcode, the conventional-commit-prefix ban, the `done` final rule). This matches the actual file contents and prevents collateral edits.

### Positive Notes
- Root-cause diagnosis is precise and independently verified against the source — not a speculative refactor.
- Tight scope: single file, two tasks (rewrite + verify), with a concrete self-check. No gold-plating.
- Reframing Step 3 around the same three exploration angles preserves the planner's intended depth while removing the unreachable branch — behavior is retained, only the mechanism changes.

PLAN_REVIEW_PASS
