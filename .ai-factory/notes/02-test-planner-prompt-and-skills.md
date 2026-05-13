# Test Planner Prompt and Skills Reference

**Date:** 2026-05-12
**Source:** conversation context

## Key Findings

- A `test-planner.md` prompt was created for the orchestrator's test pipeline agent — it lives at `orchestrator/prompts/test-planner.md`.
- The global skills library at `~/.claude/skills/` was fully synced with upstream (`https://github.com/lee-to/ai-factory`) — new skills added, existing ones updated.
- The existing orchestrator prompts (`planner.md`, `implementer.md`, `reviewer.md`, `refactor-planner.md`) already cover the same ground as the corresponding skills — no inlining needed for existing agents.

## Details

### test-planner.md

Created at `orchestrator/prompts/test-planner.md`. This is the prompt for the **TestPlanner agent** in the `test` pipeline mode described in note `01-test-pipeline-mode.md`.

**What it does:**
1. Reads the milestone — the milestone already specifies what to test (files, classes, functions)
2. Reads the source code of target files in full — derives edge cases, branches, error paths
3. Finds existing `*.spec.*` / `*.test.*` patterns in the project — matches the test style
4. Writes a plan where each task = one `describe` block with named `should ... when ...` test cases
5. The plan includes an explicit `Test Command` and `Target Spec File` fields for the TestRunner

**Key design decision:** TestPlanner does not decide what to test — the milestone description already contains that. Its job is to decompose the target code into concrete test cases that the Implementer can write without further analysis.

### Skills Library

All skills live at `~/.claude/skills/` (symlinked from `~/projects/skills/.claude/skills` — that repo is the source of truth for customizations).

Upstream source: `https://github.com/lee-to/ai-factory` (skills in the `skills/` subdirectory).

**Skills relevant to the test pipeline:**

| Skill | Path | Relevant section |
|-------|------|-----------------|
| `aif-best-practices` | `~/.claude/skills/aif-best-practices/SKILL.md` | `## Testing Practices` — AAA pattern, naming rules (`should [behavior] when [condition]`), coverage priorities |
| `aif-plan` | `~/.claude/skills/aif-plan/SKILL.md` | Plan file format, task granularity rules — `test-planner.md` follows the same structure |
| `aif-implement` | `~/.claude/skills/aif-implement/SKILL.md` | How the Implementer reads plans and marks checkboxes — unchanged, works for test tasks too |
| `aif-review` | `~/.claude/skills/aif-review/SKILL.md` | Code review criteria — applicable to test code quality review |
| `aif-qa` | `~/.claude/skills/aif-qa/SKILL.md` | Manual QA workflow (change-summary → test-plan → test-cases) — **not** for automated test writing, but useful reference for test coverage thinking |

**Skills added in this sync (new, not previously available):**
- `aif-ci` — CI pipeline setup
- `aif-commit` — conventional commit message generation
- `aif-dockerize` — Dockerfile generation
- `aif-qa` — manual QA workflow
- `aif-reference` — reference document generation
- `aif-rules-check` — rules compliance checking

### Sync Procedure

Documented in `~/projects/skills/CLAUDE.md` under `## Upstream Sync`. Custom skills that must never be overwritten: `detangle`, `milestone-rescue`, `roadmap-decompose`, `roadmap-prune`, `temporal-tree`, `ui-ux-pro-max`, `aif-note`.

## Open Questions

- TestRunner implementation: should it run the full suite after each fix iteration (regression safety) or only the target spec file (speed)? See note `01-test-pipeline-mode.md`.
- Should plan review (`PlanReviewer`) be skipped for test milestones to speed up the cycle?
- `process_test_milestone()` in `main.py` and the `TestRunner` class in `agents.py` are not yet implemented.
