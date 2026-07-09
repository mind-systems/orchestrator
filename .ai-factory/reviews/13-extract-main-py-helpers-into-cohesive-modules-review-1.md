# Code Review: Extract main.py helpers into cohesive modules

## Scope
Reviewed the full diff (`git diff HEAD`, `git status`): three new modules (`orchestrator/usage.py`, `orchestrator/resume.py`, `orchestrator/runtime.py`), the rewired `orchestrator/main.py`, and repointed imports in `tests/test_main.py`. Read each new file and the retained code in full.

## Verification performed
- **No import cycle.** `import orchestrator.main / usage / resume / runtime` all load cleanly. `usage` imports `config`+`agents`; `resume` imports `agents`+stdlib; `runtime` imports `state`+`notify`+`agents`. None import `main`. Downward-only, as the spec requires.
- **Pure move, no behaviour drift in retained code.** The `main.py` diff adds *only* import lines (0 added non-import lines); every other change is a deletion of a moved function. Retained functions (`process_milestone`, loops, `_git_commit`, `run_*`, `cli`, `Mode`/`IMPLEMENT_MODE`/`TEST_MODE`) are untouched.
- **Moved bodies are verbatim.** `_parse_pct`, `_check_usage_limits`, `_validate_sidecar_step`, `_detect_step`, the two detector wrappers, `_handle_sigint`, `_fmt_elapsed`, `_run_elapsed`, `_with_caffeinate` match their originals. The `SESSION_PATTERN`/`WEEKLY_PATTERN` constants hold the exact regex strings previously inlined at `main.py:97-98`.
- **Wrapper literals match `Mode`.** `resume._detect_milestone_step` → `review` / `review_failed:` / `-review-{n}.md` / `REVIEW_PASS`; `_detect_test_milestone_step` → `test_run` / `test_run_failed:` / `-test-{n}.txt` / `TEST_PASS`. Identical to `IMPLEMENT_MODE`/`TEST_MODE`. The production call at the former `main.py:346` still calls `_detect_step` directly with `mode.*` fields; argument order matches the new signature.
- **Unused imports cleaned correctly.** `import re` and `kill_active_child` dropped from `main.py` (both were only used by moved code); `import signal` retained (still registers the handler in `run_implement`/`run_test`). `_read_sessions`/`_write_session`/`HaltError`/`PipelineStopError` retained and still used.
- **Tests repointed as Class-A drift only.** `_parse_pct`/`_check_usage_limits` from `orchestrator.usage`; the detectors + `_validate_sidecar_step` from `orchestrator.resume`; `process_milestone` from `orchestrator.main`. The single monkeypatch retarget (`main_module.subprocess` → `usage_module.subprocess`) is required because `_check_usage_limits` now resolves `subprocess` in `usage`'s namespace — correct, and no assertion was weakened.
- **`uv run pytest`: 91 passed.**

## Findings
None. The extraction is behaviour-preserving, cycle-free, and the test suite is green.

REVIEW_PASS
