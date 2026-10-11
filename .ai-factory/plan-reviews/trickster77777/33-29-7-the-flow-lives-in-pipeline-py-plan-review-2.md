## Plan Review Summary

**Plan:** `.ai-factory/plans/trickster77777/33-29-7-the-flow-lives-in-pipeline-py.md` (revision 2)
**Task:** 29.7 — the flow lives in `pipeline.py` (roadmap `.ai-factory/roadmaps/trickster77777.md`, spec `.ai-factory/specs/trickster77777/0074-the-flow-lives-in-pipeline.md`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** In `.ai-factory/ARCHITECTURE.md`, § Dependency Rules puts `pipeline.py` in "The flow" layer, and its one in-layer edge is `pipeline` → `resume`. The planned `pipeline` imports all point to that edge or to lower layers: `agents`, `usage`, `notify` and `runtime` are roles and adapters; `config`, `errors`, `ports`, `protocol`, `roadmap` and `state` are vocabulary. I checked every one of those modules' imports, and none imports `main` or `pipeline`, so the move adds no cycle. After the move, `main` imports only from lower layers. § Folder Structure and § The one flow already name `pipeline.py` as the home of `process_task` and `Mode`, so "Docs: no" holds for ARCHITECTURE.md. Its line about `_implement_loop` and `_test_loop` living in `main.py` stays true.
- **Rules — WARN.** `.ai-factory/RULES.md` does not exist, so there are no explicit conventions to check.
- **Roadmap — OK.** The plan matches the 29.7 contract line and spec 0074. Adding `process_task` to `main`'s import from `pipeline` is correct and stays inside the contract line's "imports the flow from `pipeline`": both lambdas in `_implement_loop` and `_test_loop` call it.
- **Spec tree — OK.** The reviewer duty matches spec § What must be true after: on the passing round only, send one `SendMessage` to the bare session name, record the result verbatim above `REVIEW_PASS`, and do not raise `ESCALATION` if the send fails. `../skills/.ai-factory/architects/trickster77777/07/address.md` exists and carries a `session-name:` line.

### Verification against the code

I checked the plan against `orchestrator/main.py`, `tests/test_main.py` and the sibling modules as they stand now:
- **Moved symbols and their order.** The order is right: `Mode`, `IMPLEMENT_MODE`, `TEST_MODE`, (`_run_loop`), `_next_number`, `_artifact_dir`, `_git_commit`, `process_task`, `_run_dynamic_loop`. Outside `.ai-factory/`, the only occurrence of `_run_loop` in the repo is its own definition, so deleting it is safe.
- **`pipeline` imports.** The list covers every name the moved bodies look up, and nothing in it goes unused. `ParseResult` is rightly dropped.
- **`main` imports.** What remains is exactly what the CLI half uses:
  - `argparse`, `signal`, `sys`, `time` and `Path`;
  - `OrchestratorConfig` (annotations) and `load_config`;
  - the three errors, `Outcome` and `report` (used by `cli`);
  - the three `layout` helpers;
  - `_handle_sigint`, `_run_summary` and `_with_caffeinate`;
  - `state`.
- **Test patches.** The only patches on `main_module` that must move are the five in `test_process_task_escalated_sidecar_raises_without_constructing_agents`. The `_run_cli_with` patches stay valid. No other test file imports `orchestrator.main`.
- **Stale comment.** The comment `# Production patterns verbatim from main.py` does misname its home: `SESSION_PATTERN` and `WEEKLY_PATTERN` live in `orchestrator/usage.py`. Fixing it is in scope.
- **Verify steps can fail.** Revision 1's directory-only grep is fixed: it now targets `tests/test_main.py`. I ran the `main.py` grep against the current tree, and it matches (`import subprocess`, `class Mode`, `IMPLEMENT_MODE`), so it can tell a done move from an undone one. The reverse-import grep returns nothing today, as expected. The baseline `uv run pytest` gives 227 passed, which matches the plan's pinned count.

### Critical Issues

None.

### Positive Notes

- **Revision 2 fixes the plan-review-1 finding** and records why. A grep given a bare directory without `-r` prints no matches and proves nothing.
- **The plan is grounded in the code, not just the spec text.** It catches the missing `process_task` import, the dead `ParseResult` import, and which stdlib imports `main` keeps or loses.
- **Patching stays explicit.** Flow names stay module-level lookups in `pipeline`, and `cli` keeps its lookups in `main`, so every monkeypatch still hits a real attribute.
- **Moving the code verbatim and in order** keeps the change behaviour-neutral and makes the diff easy to review.

## Deferred observations

- Affects: `docs/future/run-context-refactor.md` (outside 29.7's file boundary) — This future doc names `main.py` as the home of the run loops ("read in the run loops (`main.py`)"), of the `tasks_done` increment after `mark_done`, and of `process_task` (`main.py:198`, a position address). Once 29.7 lands, all three live in `pipeline.py`. When that doc is next revised, it should cite `pipeline.py` and `process_task` by name, with no line number.

PLAN_REVIEW_PASS
