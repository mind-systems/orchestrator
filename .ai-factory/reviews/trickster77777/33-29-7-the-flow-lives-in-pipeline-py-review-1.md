## Code Review Summary

**Files Reviewed:** 3 (`orchestrator/pipeline.py` new, `orchestrator/main.py`, `tests/test_main.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** `pipeline.py` sits in "The flow" layer. It imports only from roles/adapters (`agents`, `notify`, `runtime`, `usage`) and vocabulary (`config`, `errors`, `ports`, `protocol`, `roadmap`, `state`), plus the one named in-layer edge, `pipeline` → `resume`. It imports neither `main` nor `layout`. `main` imports only from lower layers, and nothing in the package imports `main` (`grep -rn 'from \.main\|import main' orchestrator/` returns no matches). This matches § Dependency Rules and § Folder Structure.
- **Rules — WARN.** `.ai-factory/RULES.md` is absent, so there are no explicit conventions to check.
- **Roadmap — OK.** The change matches contract line 29.7 and spec `0074-the-flow-lives-in-pipeline.md`. The only departure is that `main` also imports `process_task`. The spec lists only `IMPLEMENT_MODE`, `TEST_MODE` and `_run_dynamic_loop`, but the lambdas in `_implement_loop` and `_test_loop` call `process_task`, and the contract line says "imports the flow from `pipeline`". This is conformance, not a finding.

### Verification

- **The moved code is unchanged.** I compared each moved definition in `HEAD:orchestrator/main.py` with its counterpart in `orchestrator/pipeline.py`, using AST-delimited spans and a unified diff. All eight show zero difference lines: `Mode`, `IMPLEMENT_MODE`, `TEST_MODE`, `_next_number`, `_artifact_dir`, `_git_commit`, `process_task`, `_run_dynamic_loop`. They also keep their original order.
- **What remains in `main` is unchanged.** `_test_loop`, `_implement_loop`, `run_implement`, `run_test` and `cli` are identical to HEAD. `_run_loop` is gone, and nothing referenced it.
- **Imports are complete with nothing unused.** `pipeline` imports every name its bodies look up. `main` dropped `subprocess`, `NamedTuple`, `.agents`, `.ports`, `.protocol`, `.resume`, `.roadmap` and `.usage`, which it no longer uses, along with the dead `ParseResult`. It keeps `time` and `sys`, which it still needs.
- **Patches point at the right module.** The escalated-sidecar test now patches `pipeline_module`. The `_run_cli_with` patches (`load_config`, `run_implement`, `report`) stay on `main_module` and remain valid, because `cli` still looks them up in `main`'s namespace.
- **The entry point is unchanged.** `pyproject.toml` still has `orchestrator.main:cli`, and `uv run python -c "import orchestrator.main"` succeeds.
- **Tests pass.** `uv run pytest` → 227 passed, the same count as the baseline.
- **The stale test comment is fixed.** It now says "verbatim from usage.py", which matches where `SESSION_PATTERN`/`WEEKLY_PATTERN` live.

### Critical Issues

None.

### Positive Notes

- **A pure move.** Bodies are byte-identical, so the change is behaviour-neutral by construction.
- **Module docstrings state each module's concern,** so a reader can see where `main` ends and `pipeline` begins.
- **Each patch targets the module that does the lookup,** which keeps the monkeypatches meaningful.

## Deferred observations

- Affects: `docs/future/run-context-refactor.md` — This future doc still names `main.py` as the home of the run loops ("read in the run loops (`main.py`)"), of the `tasks_done` increment after `mark_done`, and of `process_task` (`main.py:198`, a position address that has already rotted). After this task, those homes are `pipeline.py`. The file is outside 29.7's spec and file boundary. When that doc is next revised, it should cite `pipeline.py` and `process_task` by name, with no line number.

## Phase 29 notice to the skills-side architect

I read `../skills/.ai-factory/architects/trickster77777/07/address.md` at send time (`session-name: skills-f3`) and sent one `SendMessage` to `skills-f3`. Tool result, verbatim:

```
{"success":true,"message":"“Notify architect Phase 29 has landed” → skills-f3 (another Claude session on this machine; in that session's inbox, not yet read by its Claude — a [Cross-session delivery notice] follows if that session holds it (usually a different permission mode) or refuses it)","msg_id":"5a090b22-00ea-4340-b174-a44a873cb9ae"}
```

REVIEW_PASS
