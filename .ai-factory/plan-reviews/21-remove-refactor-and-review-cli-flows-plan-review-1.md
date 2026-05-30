# Plan Review: Remove `refactor` and `review` CLI flows

## Verdict

The plan is well-structured, identifies the correct deletion surface, and pre-empts the obvious failure modes (the `elif`-without-`if` trap, the stale `RefactorPlanner` import, the orphan `PlannerReviewer.patch()` method). All line-number references match the current code, all symbol names are correct, and the cross-references between tasks line up.

I verified all references to `RefactorPlanner`, `refactor`, `review_plan`, `run_review`, `run_refactor`, `process_refactor_milestone`, `_refactor_loop`, and `PlannerReviewer.patch` across the codebase. The only call sites and definitions of these symbols live in `orchestrator/agents.py` and `orchestrator/main.py` — exactly the two files the plan touches. The `docs/` directory and `CLAUDE.md`/`README.md` references are also enumerated correctly.

## Line-number / API-surface spot-checks

All confirmed against the current tree:

- `RefactorPlanner` class — `orchestrator/agents.py:378–447` ✓
- `PlannerReviewer.patch()` — `orchestrator/agents.py:266–283` ✓ (only caller is `review_plan()` in `main.py:460`)
- Import line — `orchestrator/main.py:13` ✓
- `process_refactor_milestone()` — `orchestrator/main.py:293–421` ✓
- `review_plan()` — `orchestrator/main.py:424–486` ✓
- `_refactor_loop()` — `orchestrator/main.py:787–815` ✓
- `run_refactor()` — `orchestrator/main.py:836–842` ✓
- `run_review()` — `orchestrator/main.py:846–880` ✓
- Subcommand registration loop — `orchestrator/main.py:887–892` ✓
- Dispatch `try` block — `orchestrator/main.py:901–915` ✓
- `from . import state` (line 15) — correctly preserved; `_handle_sigint` at line 20 still uses `state.stop_requested` ✓
- Refactor-planner prompt file — `orchestrator/prompts/refactor-planner.md` exists, and is loaded only via `_load_prompt("refactor-planner")` on `agents.py:388` ✓

## Things the plan got right that are easy to miss

1. **The `elif`-without-`if` SyntaxError trap (Task 9).** After removing the `if args.command == "review":` block, the surviving `elif args.command == "test":` would be a hard `SyntaxError` at import time. The plan calls this out and shows the correct final shape.
2. **Keeping `from . import state` (Task 3).** Easy to over-delete since `state.stop_requested` is the only use in this module after the cuts; the plan explicitly preserves it.
3. **The orphaned `PlannerReviewer.patch()` (Task 1b).** This method is only called by `review_plan()` in `main.py:460` — it would otherwise be dead code after Phase 1.
4. **Atomic Phase-1 commit reasoning.** The justification ("intermediate states would break `import` for every subcommand") is correct: e.g. deleting the `RefactorPlanner` class while `main.py` still imports it would `ImportError` at startup of `implement`/`test` too, not just `refactor`. The Task-9b smoke-check (`uv run orchestrator --help`) is a sensible final gate.
5. **`docs/configuration.md` line 5 fix.** Changing `refactor` → `test-run` in the env-var description closes a pre-existing doc gap: the same `ORCHESTRATOR_MAX_ITERATIONS` constant already scoped the test-run loop silently. Good catch.
6. **`CLAUDE.md` "Four-agent pipeline" count.** Currently the heading says "Four-agent pipeline" but lists five numbered items — a pre-existing inconsistency. Removing the `RefactorPlanner` bullet makes the count truthful (4: PlannerReviewer, PlanReviewer, Implementer, TestRunner). Plan handles this correctly.

## Minor issues (non-blocking)

### 1. `configuration.md` line 11 — drops mention of `process_test_milestone()`

The plan rewrites line 11 from:

> Модели передаются при создании агентов в `process_milestone()` и `process_refactor_milestone()`.

to:

> Модели передаются при создании агентов в `process_milestone()`.

But agents are also instantiated in `process_test_milestone()` at `main.py:620–622` (and `PlannerReviewer` is constructed there with `planner_prompt_name="test-planner"`). The truthful replacement is:

> Модели передаются при создании агентов в `process_milestone()` и `process_test_milestone()`.

This is a pre-existing imprecision (the current text already omits `process_test_milestone`), and the plan doesn't make it worse — but since the doc is being touched anyway, it would cost nothing to fix.

### 2. `CLAUDE.md` "default models" bullet — same omission

The proposed rewrite leaves the bullet as:

> Default models/effort: PlannerReviewer=opus/high, PlanReviewer=opus/high, Implementer=sonnet/high — override when instantiating agents in `process_milestone()`

Same observation: `process_test_milestone()` also instantiates agents. Recommend appending `and process_test_milestone()` for accuracy. Non-blocking.

### 3. Extra blank line between `run_test` and `run_review`

Current `main.py:833–846` has three blank lines (834, 835, 844, 845) between `run_test` and `run_review` due to a stray extra blank above `run_review`. After Task 7 deletes lines 836–842 (`run_refactor`), the implementer needs to be careful to collapse to exactly two blank lines between `run_test` and what was the next surviving top-level def. The plan's "preserve two-blank-line spacing" instruction covers this in spirit; just flagging that the implementer should *normalize* rather than just delete the labelled range verbatim.

### 4. `README.md` line 5 — "пятиступенчатый конвейер" is not touched

The opening sentence describes a five-step pipeline (Planner → PlanReviewer → Implementer → Reviewer → commit) and is unaffected by this plan. Out of scope; just noting that the count is still arguable after the removal — but the description is about the `implement` pipeline only, so leaving it alone is the right call.

### 5. `CLAUDE.md` `--output-format json` mismatch

Line 61 of `CLAUDE.md` says `_run_claude()` uses `--output-format json`, but the actual code uses `--output-format stream-json` (see `agents.py:70`). Pre-existing bug, completely out of scope for this plan. Mentioning only because Task 10 edits `CLAUDE.md`; if the implementer wants to opportunistically correct it, the trip cost is near zero.

## Context Gates

- **ARCHITECTURE.md**: not present in `.ai-factory/` — no architectural-boundary check available. WARN (optional file missing, not blocking for this task).
- **RULES.md**: not present in `.ai-factory/` — no explicit project-rule check available. WARN.
- **ROADMAP.md**: present. The milestone "Remove refactor and review CLI flows" appears as an active task. Linkage is consistent.
- **CLAUDE.md (project)**: the global rule "Plan → STOP" is respected — this artifact is a review of the existing plan, not an implementation.

## Critical Issues

None. The plan is execution-ready.

## Positive Notes

- Every task lists the file(s) it touches and the precise line range.
- The Phase-1 / Phase-2 split correctly separates code-correctness changes (one atomic commit) from documentation cleanup (a second commit), matching the actual coupling of the changes.
- Russian-language preservation for `docs/` and `README.md` is explicitly called out and matches the user's global rule "Match the language of existing docs."
- Task 9b adds an executable smoke gate before the commit — exactly the right place to catch the `elif`/`ImportError` class of bugs.
- The plan documents *why* the tasks are bundled into a single commit (intermediate states break `import`), not just *what* to do.

PLAN_REVIEW_PASS
