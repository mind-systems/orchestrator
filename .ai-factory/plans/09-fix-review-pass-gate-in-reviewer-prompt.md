# Plan: Fix REVIEW_PASS gate in reviewer prompt

## Context
The code reviewer bypasses the REVIEW_PASS gate by writing findings under non-standard headings (`## Bugs`, `## Issues`) that don't match the section names checked by the prompt rules. The fix makes the gate content-based — if any finding was written under any heading, REVIEW_PASS is blocked — and removes the `### Suggestions` section which created a false distinction between "blocking" and "non-blocking" findings.

## Settings
- Testing: no
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Fix reviewer prompt

- [x] **Task 1: Replace REVIEW_PASS rules in reviewer.md**
  Files: `orchestrator/prompts/reviewer.md`
  In the `## Output Format` section, replace the current `**REVIEW_PASS rules:**` block (lines 103–107) with content-based rules. New text:
  ```
  **REVIEW_PASS rules:**
  - Write `REVIEW_PASS` only if you have no findings at all — every findings section you wrote is empty.
  - If you wrote even one bug, issue, or problem under any heading, do not write `REVIEW_PASS`.
  - If there is truly nothing to flag, end the review file with `REVIEW_PASS` on its own line and include it in your text response.
  ```
  This removes all references to specific section names (`critical issues`, `suggestions`) and makes the gate purely about whether any finding text exists.

- [x] **Task 2: Remove `### Suggestions` section from the output format template**
  Files: `orchestrator/prompts/reviewer.md`
  In the markdown code block inside `## Output Format` (lines 84–101), delete the two lines for the Suggestions section:
  ```
  ### Suggestions
  [Nice to have improvements]
  ```
  This eliminates the false "blocking vs non-blocking" split. All findings go under `### Critical Issues` or any heading the reviewer chooses — and any finding blocks PASS.

- [x] **Task 3: Update the reinforcement prompt in `PlannerReviewer.review()`**
  Files: `orchestrator/agents.py`
  Line 203 currently says `"If no critical issues found, end the review file with REVIEW_PASS on its own line.\n"`. Replace with `"If you have no findings at all, end the review file with REVIEW_PASS on its own line.\n"`. This aligns the runtime reinforcement with the updated prompt — no reference to specific section names.
