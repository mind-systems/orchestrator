## Plan Review Summary

**Plan:** 13 — Extract main.py helpers into cohesive modules
**Files Reviewed:** plan + `orchestrator/main.py`, `orchestrator/state.py`, `orchestrator/agents.py` (imports), `orchestrator/notify.py` (imports), `tests/test_main.py`, spec `09-extract-main-modules.md`, `ARCHITECTURE.md`, `ROADMAP.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Roadmap** (WARN → resolved): The plan's `# Plan:` heading matches the roadmap contract line "Extract main.py helpers into cohesive modules". The line mandates this task run **last, after 05 and 06**. Both are complete: spec-05 (`HaltError`/yellow-halt, commit landed) and spec-06 (unify pipeline, `cbbbe11`) are `[x]`. `main.py` already carries the settled forms — the unified `_detect_step` with wrapper detectors and `_handle_sigint` reading `state.config`/`state.project_dir`. Ordering constraint satisfied.
- **Spec (`09-extract-main-modules.md`)**: The plan faithfully implements the spec's three-cluster boundary (`usage.py` / `resume.py` / `runtime.py`), the "move-only, no behaviour change" rule, downward-imports-only invariant, and the explicit "keep in `main.py`" / "do NOT touch" lists. The plan's Task-2 wrapper-literal handling is the correct consequence of the no-cycle boundary the spec names.
- **Architecture** (WARN, out of scope): `ARCHITECTURE.md` describes a ~5-file layered layout (`main`/`agents`/`roadmap`/`state`) and will not mention the three new modules after this task. The spec **explicitly forbids touching `ARCHITECTURE.md`**, so the plan correctly leaves it alone. The new modules import downward (`agents`/`config`/`notify`/`state` + stdlib), consistent with the documented dependency direction — no layering violation, only a documentation-freshness gap deferred below.
- **Rules / skill-context**: No `.ai-factory/RULES.md` and no `.ai-factory/skill-context/` present — gates skipped.

### Critical Issues
None.

### Verification notes (all confirmed correct)
- **Line references are exact.** `_parse_pct`/`_check_usage_limits` (82–121), `_validate_sidecar_step` (166–212), `_detect_step` (215–301), `_detect_milestone_step` (304–313), `_detect_test_milestone_step` (316–325), `_handle_sigint` (71–79), `_fmt_elapsed` (490–493), `_run_elapsed` (496–499), `_with_caffeinate` (502–527) — every span matches `main.py`.
- **Wrapper literals match `Mode` fields exactly.** Task 2's implement literals (`review` / `review_failed:` / `-review-{n}.md` / `REVIEW_PASS`) and test literals (`test_run` / `test_run_failed:` / `-test-{n}.txt` / `TEST_PASS`) are byte-for-byte the `IMPLEMENT_MODE`/`TEST_MODE` values at lines 44–52 / 62–67. No behaviour drift.
- **No import cycle.** `agents.py` imports only `state` + stdlib; `notify.py` imports only `urllib`/`typing`. Neither imports `main`. The new modules import from `agents`/`config`/`notify`/`state` downward only — clean.
- **`main.py` import cleanup is precise.** `re` is used solely by `_parse_pct` (no other `re.` call in `main.py`), so dropping it is safe. `kill_active_child` is referenced only inside `_handle_sigint` (line 74), so removing it from the `.agents` line is safe. Retained symbols (`subprocess`, `sys`, `time`, `signal`, `_read_sessions`, `_write_session`, `HaltError`, `PipelineStopError`, the four agent classes) all have remaining uses in `main.py`.
- **Only `_detect_step` need be imported into `main.py`.** Production calls `_detect_step` directly (line 346); the two wrapper detectors are used exclusively by the test suite — so they belong in `resume.py` and `main.py` needs no import of them. Correct.
- **Test repointing is complete and the monkeypatch fix is the sharp catch.** After `_check_usage_limits` moves to `usage.py`, its `subprocess.run` resolves via `usage`'s module namespace; `test_check_usage_limits_raises_halt_error_over_threshold` (line 756) must patch `usage_module.subprocess`, not `main_module.subprocess`. The plan calls this out and adds `from orchestrator import usage as usage_module`. All other `main_module` references in the tests (`load_config`, `run_implement`, `notify`, `cli`) target symbols that stay in `main.py`, so they remain valid.
- **No external consumers.** A repo-wide search shows the moved symbols are referenced only in `main.py` and `tests/test_main.py` (plus prose artifacts). No other production module imports them.

### Positive Notes
- The Assumption block (lines 17–18) pre-empts the one genuinely non-obvious move — inlining `Mode`-field literals into the relocated wrappers to break the `resume → main` cycle — and ties the values to the stable step vocabulary. This is exactly the kind of decision that otherwise gets guessed wrong at implement time.
- Task 4 enumerates the retained imports explicitly rather than leaving "clean unused imports" to interpretation, which removes the risk of over-pruning `signal`/`subprocess`.
- Two-commit split (new modules, then rewire+tests) keeps each commit independently reasoned; the "green before and after" verify gate is stated concretely.

## Deferred observations
- Affects: future docs/architecture sweep (the roadmap's remaining post-STOP work, or a dedicated doc task) — `ARCHITECTURE.md` will describe the pre-split module set (`main`/`agents`/`roadmap`/`state`) and omit `usage.py`/`resume.py`/`runtime.py` and their downward dependency edges. This milestone's governing spec explicitly forbids touching `ARCHITECTURE.md`, so the staleness is an intentional scope exclusion, not a defect in this plan; it should be reconciled whenever the architecture doc is next refreshed (the doc's own "Structured Modules at ~10 modules" evolution trigger is the natural moment).

PLAN_REVIEW_PASS
