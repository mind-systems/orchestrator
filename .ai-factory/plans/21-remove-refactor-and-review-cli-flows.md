# Plan: Remove `refactor` and `review` CLI flows

## Context
Delete the `refactor` and `review` pipelines (functions, agent class, prompt, subcommands, and the now-orphaned `PlannerReviewer.patch()` method) from the orchestrator so only `implement` and `test` remain. Also update user-facing documentation (`CLAUDE.md` and the `docs/` directory) so it no longer advertises the removed modes. Keep all implement/test infrastructure untouched.

## Settings
- Testing: no
- Logging: minimal
- Docs: yes (CLAUDE.md + docs/)

## Tasks

### Phase 1: Code surgery — remove all refactor/review code in one atomic edit

Tasks 1–9 must all be applied before the next commit. Splitting them produces a broken intermediate state (e.g. removing `PlannerReviewer.patch()` while `review_plan()` still calls it, or leaving the `RefactorPlanner` import while the class is gone — both fail at `import` time for every subcommand). They are listed in a logical order, but the dependency edges between them are tight enough that they should be staged together and committed as one unit.

- [x] **Task 1: Delete the `RefactorPlanner` class from `orchestrator/agents.py`**
  Files: `orchestrator/agents.py`
  Remove the entire `RefactorPlanner` class (currently lines 378–447), including its `__init__`, `audit_and_plan`, and `verify` methods. Stop at the blank line(s) immediately before `class TestRunner:`. Preserve PEP-8 two-blank-line spacing between the remaining top-level classes (`PlannerReviewer`, `PlanReviewer`, `Implementer`, `TestRunner`). Do not touch `PlannerReviewer`, `PlanReviewer`, `Implementer`, `TestRunner`, `_load_prompt`, `_run_claude`, `_read_sessions`, `_write_session`, `PipelineStopError`, or `RateLimitError`.

- [x] **Task 1b: Delete `PlannerReviewer.patch()` from `orchestrator/agents.py`**
  Files: `orchestrator/agents.py`
  Remove the `patch()` method (currently lines 266–283), starting at the `def patch(...)` line and ending at the blank line before `class PlanReviewer:`. This method's only call site is `review_plan()` in `main.py:460`, which is deleted in Task 5. Keep the PEP-8 two-blank-line separator between `class PlannerReviewer:` and `class PlanReviewer:`.

- [x] **Task 2: Delete the refactor-planner prompt file**
  Files: `orchestrator/prompts/refactor-planner.md`
  Remove the file from the repo (`git rm` or delete). It is only referenced by `RefactorPlanner` via `_load_prompt("refactor-planner")`, which is gone after Task 1.

- [x] **Task 3: Update the import in `orchestrator/main.py` to drop `RefactorPlanner`**
  Files: `orchestrator/main.py`
  In the import on line 13, remove `RefactorPlanner` from the imported names so the line becomes:
  `from .agents import Implementer, PipelineStopError, PlannerReviewer, PlanReviewer, RateLimitError, TestRunner, _read_sessions, _write_session`
  Keep `from . import state` on line 15 — `_handle_sigint` still uses `state.stop_requested`. Keep all other imported names exactly as they are.

- [x] **Task 4: Delete `process_refactor_milestone()` from `orchestrator/main.py`**
  Files: `orchestrator/main.py`
  Remove the entire `process_refactor_milestone()` function (currently lines ~293–421), including its docstring. Preserve **two blank lines** between the surviving top-level functions, matching PEP-8 / the rest of the file (`main.py` consistently uses two blank lines between top-level defs — see lines 60–63, 146–149, 290–293, 421–424). Do not touch `process_milestone()` above it or `review_plan()` below it (that one is removed in Task 5).

- [x] **Task 5: Delete `review_plan()` from `orchestrator/main.py`**
  Files: `orchestrator/main.py`
  Remove the entire `review_plan()` function (currently lines ~424–486). Its only caller is `run_review()` (Task 8). Preserve two-blank-line spacing between the surviving top-level functions.

- [x] **Task 6: Delete `_refactor_loop()` from `orchestrator/main.py`**
  Files: `orchestrator/main.py`
  Remove `_refactor_loop()` (currently lines ~787–815). Preserve two-blank-line spacing. Keep `_implement_loop()`, `_test_loop()`, and `_run_loop` untouched — they are still used by the remaining flows.

- [x] **Task 7: Delete `run_refactor()` from `orchestrator/main.py`**
  Files: `orchestrator/main.py`
  Remove `run_refactor()` (currently lines ~836–842). Preserve two-blank-line spacing. Keep `run_implement()` and `run_test()` untouched.

- [x] **Task 8: Delete `run_review()` from `orchestrator/main.py`**
  Files: `orchestrator/main.py`
  Remove `run_review()` (currently lines ~846–880), including its inner `_already_passed()` and `loop()` helpers. Preserve two-blank-line spacing. Keep `_with_caffeinate` and the surrounding functions untouched.

- [x] **Task 9: Update `cli()` to drop `refactor` and `review` subcommands and dispatch branches**
  Files: `orchestrator/main.py`
  In the subcommand registration loop (currently ~lines 887–892), remove the `("review", ...)` and `("refactor", ...)` tuples so only `("implement", ...)` and `("test", ...)` remain.
  In the dispatch `try` block (currently ~lines 901–915), delete the `if args.command == "review":` block (including its caffeinate/loop call) and the `elif args.command == "refactor":` branch. **Then convert the surviving `elif args.command == "test":` to `if args.command == "test":`** — an `elif` without a preceding `if` is a `SyntaxError`. The final shape inside the `try:` must be exactly:
  ```python
  try:
      if args.command == "test":
          run_test(project_dir, max_iterations)
      else:
          run_implement(project_dir, max_iterations)
  except PipelineStopError as e:
      ...
  except RateLimitError as e:
      ...
  ```
  Keep the two `except` blocks (`PipelineStopError`, `RateLimitError`) exactly as they are.

- [x] **Task 9b: Smoke-check `cli()` after edits**
  Files: (none modified)
  Run `uv run orchestrator --help` from the repo root. Confirm exit code 0 and that only `implement` and `test` appear in the subcommand list. This catches `ImportError` (left-behind `RefactorPlanner` import), `SyntaxError` (the `elif`→`if` trap from Task 9), and `AttributeError` on any orphan call site. If it fails, fix before committing.

### Phase 2: Documentation

These tasks are documentation-only and can be committed separately from Phase 1.

- [x] **Task 10: Update `CLAUDE.md` to reflect the trimmed CLI and agent set** (depends on Task 9)
  Files: `CLAUDE.md`
  In the **Commands** section, delete the `uv run orchestrator review /path/to/project` and `uv run orchestrator refactor /path/to/project` examples (and their accompanying `# ...` comments). Keep `implement`, `test`, and the default-on-current-dir examples.
  In the **Architecture** section, change "Four-agent pipeline" to "Four-agent pipeline" by simply dropping the `RefactorPlanner` bullet — the remaining four (PlannerReviewer, PlanReviewer, Implementer, TestRunner) keep the count at four. Renumber the list 1–4:
  1. **PlannerReviewer** (unchanged)
  2. **PlanReviewer** (unchanged)
  3. **Implementer** (unchanged)
  4. **TestRunner** (unchanged content, now item 4 — keep "No LLM." wording).
  Delete the **RefactorPlanner** bullet entirely. Remove any mention of `process_refactor_milestone()` from the prose; keep the `implement` and `test` pipeline diagrams.
  In the **Key constants** section, change the `ORCHESTRATOR_MAX_ITERATIONS` description from `(plan review, implement review, refactor verify)` to `(plan review, implement review, test run)` — drops the refactor reference and closes a pre-existing doc gap.
  In the default-models bullet, remove `RefactorPlanner=opus/high` and the `process_refactor_milestone()` reference, leaving only `PlannerReviewer=opus/high, PlanReviewer=opus/high, Implementer=sonnet/high — override when instantiating agents in process_milestone()`.

- [x] **Task 11: Update `docs/` and `README.md` to drop refactor-mode references** (depends on Task 9)
  Files: `docs/refactor-mode.md` (delete), `docs/configuration.md` (edit), `README.md` (edit).
  **Match the language of existing docs**: both `docs/configuration.md` and `README.md` are written in Russian — preserve Russian in all edits. Do not translate or rewrite in English.
  Delete `docs/refactor-mode.md` outright — it documents only the removed `refactor` mode.
  In `docs/configuration.md`:
  - Line 5: change `план-ревью, implement-ревью, refactor` to `план-ревью, implement-ревью, test-run` (drop `refactor`, add the `test` mode's iteration loop that was already silently scoped by this env var).
  - Line 9: delete the sentence `RefactorPlanner работает на Opus с высоким усилием — аудит и верификация в одной сессии.` Keep the descriptions of PlannerReviewer, Implementer, and PlanReviewer.
  - Line 11: change `Модели передаются при создании агентов в process_milestone() и process_refactor_milestone().` to `Модели передаются при создании агентов в process_milestone().`
  In `README.md`:
  - Remove the `| review | … |` and `| refactor | … |` rows from the "Режимы работы" table.
  - Remove the `| [Режим рефакторинга](docs/refactor-mode.md) | … |` row from the doc-index table — this link becomes broken after `docs/refactor-mode.md` is deleted.
  Verify (grep) that `docs/how-it-works.md`, `docs/test-mode.md`, `docs/workflow.md`, and `docs/target-project.md` do not reference `refactor`, `RefactorPlanner`, `review` CLI mode, `run_review`, `run_refactor`, `process_refactor_milestone`, or `review_plan`. Current grep shows none do — if any are found during implementation, edit them too in the same task.

## Commit Plan
- **Commit 1** (after Tasks 1, 1b, 2, 3, 4, 5, 6, 7, 8, 9, and 9b smoke-check passes): "Remove refactor and review CLI flows"
  All code deletions in a single atomic commit. Intermediate states (e.g. agent class deleted while `main.py` still imports it, or `PlannerReviewer.patch()` deleted while `review_plan()` still calls it) would break `uv run orchestrator --help` for every subcommand, so they must not appear at any commit boundary.
- **Commit 2** (after Tasks 10, 11): "Update docs to drop refactor and review references"
  Pure documentation cleanup — `CLAUDE.md`, `docs/refactor-mode.md` deletion, `docs/configuration.md` edits.
