## Plan Review Summary

**Plan:** `.ai-factory/plans/trickster77777/33-29-7-the-flow-lives-in-pipeline-py.md`
**Task:** 29.7 — the flow lives in `pipeline.py` (roadmap `.ai-factory/roadmaps/trickster77777.md`, spec `.ai-factory/specs/trickster77777/0074-the-flow-lives-in-pipeline.md`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `.ai-factory/ARCHITECTURE.md` § Folder Structure already names `pipeline.py` ("The flow: process_task, Mode and its instances, the roadmap loop, _artifact_dir, the commit step"), and § The one flow / § What varies already put `process_task` and `Mode` there. The planned `pipeline` imports (`agents`, `config`, `errors`, `notify`, `ports`, `protocol`, `resume`, `roadmap`, `runtime`, `usage`, `state`) all point to the roles/adapters or vocabulary layers, plus the one named in-layer edge `pipeline → resume`. None of those modules imports `main` or `pipeline`, so the move adds no cycle. After the move, `main` imports only from lower layers, and nothing imports `main`. That matches § Dependency Rules.
- **Rules — WARN.** `.ai-factory/RULES.md` is absent, so there are no explicit conventions to check.
- **Roadmap — OK.** The plan matches the contract line for 29.7 and its spec. It also correctly widens "`main` imports `IMPLEMENT_MODE`, `TEST_MODE` and `_run_dynamic_loop`" to include `process_task`, because the lambdas in `_implement_loop` and `_test_loop` call it. That is consistent with the contract line's "imports the flow from `pipeline`".
- **Spec tree — OK.** The reviewer duty (send one `SendMessage` to the architect named in `../skills/.ai-factory/architects/trickster77777/07/address.md` on the passing round only, record the result above `REVIEW_PASS`, no `ESCALATION` on failure) matches spec § What must be true after. The address file exists.

### Verification against the code

I checked these against `orchestrator/main.py` and `tests/test_main.py` as they stand now:
- **Moved symbols and order.** The symbols to move and their order are right: `Mode`, `IMPLEMENT_MODE`, `TEST_MODE`, `_next_number`, `_artifact_dir`, `_git_commit`, `process_task`, `_run_dynamic_loop`. `_run_loop` sits between `TEST_MODE` and `_next_number`, and nothing calls it.
- **`pipeline` imports.** The planned import list covers every name the moved bodies look up: `subprocess`, `time`, `Path`, `NamedTuple`, the three roles, both verify instances, `OrchestratorConfig`, the three errors, `Outcome`/`report`, `VerifyKind`, `_read_sessions`/`_write_session`, `_detect_step`, `mark_done`/`mark_skipped`/`parse_roadmap`, `_run_summary`, `_check_usage_limits` and `state`. Nothing in the list goes unused.
- **`main` imports.** The remaining `main` imports are exactly what `_test_loop`, `_implement_loop`, `run_implement`, `run_test` and `cli` use. `ParseResult` is indeed unused today.
- **Test patches.** The `main_module` patches at `test_process_task_escalated_sidecar_raises_without_constructing_agents` are the only ones that must move. The `_run_cli_with` patches on `load_config`, `run_implement` and `report` stay valid.
- **Stale test comment.** The comment above `SESSION_PATTERN` does misname its home ("verbatim from main.py"). Fixing it inside the touched test file is in scope.

### Critical Issues

1. **The first verify grep can never fail, so it checks nothing.** In § Tests follow the owner → Verify, the plan runs `grep -nE 'main_module, "(PlannerReviewer|Implementer|PlanReviewer|mark_done|_git_commit)"' tests/` and expects no matches. Without `-r`, grep given a directory prints `grep: tests/: Is a directory`, exits 2 and prints no match lines. I ran it against the current tree, where all five patches are still on `main_module`: it reports no matches. The check therefore "passes" whether or not the implementer moved the patches. The pytest run would still catch a missed patch, since it would raise `AttributeError`, but the step as written is wrong.
   **Fix:** target the file, or recurse:
   ```bash
   grep -nE 'main_module, "(PlannerReviewer|Implementer|PlanReviewer|mark_done|_git_commit)"' tests/test_main.py
   # or
   grep -rnE 'main_module, "(PlannerReviewer|Implementer|PlanReviewer|mark_done|_git_commit)"' tests/
   ```

### Positive Notes

- **The plan grounds itself in the code** rather than the spec text alone. It catches the `process_task` import the spec omits, the dead `ParseResult` import, and that `main` no longer needs `subprocess`/`NamedTuple` but keeps `time`/`sys`.
- **Patch-ability is stated explicitly.** Every name the flow looks up stays a module-level lookup in `pipeline`, and `cli` keeps looking up `load_config`, `run_implement` and `report` in `main`. Both keep the monkeypatches meaningful.
- **"Verbatim, in their current order" keeps the move behaviour-neutral** and makes the diff easy to review.
- **The other verify steps are concrete:** the `main.py` grep, the reverse-import grep, the pinned test count (227) and the import smoke test.

## Deferred observations

- Affects: `docs/future/run-context-refactor.md` (a docs owner outside 29.7's file boundary) — This future doc names `main.py` as the home of the run loops ("read in the run loops (`main.py`)"), of the `tasks_done` increment after `mark_done`, and of `process_task` (`main.py:198`, a position address that has already rotted). Once 29.7 lands, those homes are `pipeline.py`. The fix is outside this task's spec, which touches only `main.py`, `pipeline.py` and `tests/test_main.py`. It should cite `pipeline.py` and `process_task` by name, without a line number, when that doc is next revised.
