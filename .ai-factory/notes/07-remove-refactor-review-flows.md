# Remove `refactor` and `review` CLI Flows

Keep only `implement` and `test`. Delete everything related to refactor and review pipelines.

## What to delete

### `orchestrator/agents.py`

- `PlannerReviewer.patch()` method (only call site is `review_plan()` in `main.py` — removed below)
- `RefactorPlanner` class entirely

### `orchestrator/main.py`

Remove these functions entirely:
- `process_refactor_milestone()`
- `review_plan()`
- `_refactor_loop()`
- `run_refactor()`
- `run_review()`

Update `cli()`:
- Remove `"refactor"` and `"review"` from subcommands list
- Remove their dispatch branches; convert surviving `elif args.command == "test":` to `if args.command == "test":` (otherwise `SyntaxError`)

Update the import on `main.py:13` — remove `RefactorPlanner`.

All code deletions must land in a **single atomic commit** — removing `RefactorPlanner` without dropping its import causes `ImportError` on startup; removing `patch()` without removing `review_plan()` causes `AttributeError`. No broken intermediate state at any commit boundary.

### `orchestrator/prompts/refactor-planner.md`

Delete the file.

### `CLAUDE.md`

- Commands section: remove `review` and `refactor` examples
- Architecture section: drop `RefactorPlanner` bullet, renumber list 1–4 (PlannerReviewer, PlanReviewer, Implementer, TestRunner)
- Key constants: change `(plan review, implement review, refactor verify)` to `(plan review, implement review, test run)`
- Default models: remove `RefactorPlanner=opus/high` and `process_refactor_milestone()` reference

### `docs/`

- Delete `docs/refactor-mode.md` outright
- Edit `docs/configuration.md` (written in Russian — preserve Russian):
  - Line 5: `план-ревью, implement-ревью, refactor` → `план-ревью, implement-ревью, test-run`
  - Line 9: delete `RefactorPlanner работает на Opus с высоким усилием — аудит и верификация в одной сессии.`
  - Line 11: remove `и process_refactor_milestone()` from model-override note
- Verify `docs/how-it-works.md`, `docs/test-mode.md`, `docs/workflow.md`, `docs/target-project.md` don't reference removed flows

### `README.md`

Written in Russian — preserve Russian in all edits.
- Remove `| review | … |` and `| refactor | … |` rows from "Режимы работы" table
- Remove `| [Режим рефакторинга](docs/refactor-mode.md) | … |` row from doc-index table (broken link after `docs/refactor-mode.md` is deleted)

## What to keep untouched

- `_detect_milestone_step()`, `_detect_test_milestone_step()` — keep as-is
- `process_milestone()`, `_implement_loop()`, `run_implement()`
- `process_test_milestone()`, `_test_loop()`, `run_test()`
- `_run_loop` — still used by `_implement_loop` and `_test_loop`
- `PlannerReviewer`, `PlanReviewer`, `Implementer`, `TestRunner`
- All prompts except `refactor-planner.md`
