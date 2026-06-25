# Test Roadmap

> Unit tests for orchestrator's pure-logic functions — the ones that fail silently and drive pipeline pass/fail decisions.

## Infra

- [ ] **pytest setup** — Add `pytest` as a dev dependency: `uv add --dev pytest`. Create `tests/__init__.py` (empty) and `tests/conftest.py` (empty, placeholder for shared fixtures). Verify `uv run pytest --collect-only` exits 0 with "no tests ran". Add `## Test Command` section to each subsequent plan file: `` `uv run pytest tests/ -v` ``.

## agents.py

- [ ] **`_has_signal` unit tests** — `tests/test_agents.py`. Import directly: `from orchestrator.agents import _has_signal` (requires lazy `_CLAUDE_BIN` fix to be landed first). Cases: (1) exact signal on last line → True; (2) exact signal on line 3 of 5 (within last-5 window) → True; (3) signal on line 6 of 10 (outside last-5 window) → False; (4) signal as substring of longer word (`"no REVIEW_PASS here"`) → False; (5) empty text → False; (6) signal with trailing whitespace in file (`.strip()` path) → True; (7) `PLAN_REVIEW_PASS` variant → True.

- [ ] **`_extract_test_command` unit tests** — `tests/test_agents.py`. Import: `from orchestrator.agents import TestRunner`. Use `tmp_path` to write plan files. Cases: (1) `## Test Command` + backtick-wrapped command → command string without backticks; (2) bare command (no backticks) → command string; (3) no `## Test Command` section → None; (4) section present but body is blank before next `##` → None; (5) command is first non-empty non-heading line after the section header.

## main.py

- [ ] **`_parse_pct` unit tests** — `tests/test_main.py`. Import: `from orchestrator.main import _parse_pct`. Cases: (1) session pattern matches `"Current session: 85%"` → 85.0; (2) weekly pattern matches `"Current week (all models): 42.5%"` → 42.5; (3) no match → None; (4) decimal value `"12.3%"` → 12.3; (5) text with unrelated numbers doesn't confuse the regex.

- [ ] **`_validate_sidecar_step` unit tests** — `tests/test_main.py`. Import: `from orchestrator.main import _validate_sidecar_step`. Use `tmp_path` to create/omit artifact files. Cases: (1) empty string → `""`; (2) `"planned"` → `"planned"`; (3) `"implemented"` → `"implemented"`; (4) `"plan_review_failed:2"` with `plan-review-2.md` present → valid; (5) `"plan_review_failed:2"` with file missing → `""`; (6) `"plan_reviewed"` with a file ending `PLAN_REVIEW_PASS` → valid; (7) `"plan_reviewed"` with no passing file → `""`; (8) `"review_failed:1"` with `review-1.md` present → valid; (9) `"review_failed:1"` with file missing → `""`; (10) malformed `"plan_review_failed:abc"` → `""`; (11) unrecognized value → returned as-is.

- [ ] **`_detect_milestone_step` unit tests** — `tests/test_main.py`. Import: `from orchestrator.main import _detect_milestone_step`. Use `tmp_path` + `subprocess.run(["git", "init"], ...)` + `subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], ...)` for a real minimal git repo. Cases: (1) no plan file → `("plan", 1, plan_path)`; (2) plan exists, sidecar step=`"planned"` → `("plan_review", 1, plan_path)`; (3) sidecar step=`"plan_reviewed"`, clean git → `("implement", 1, plan_path)`; (4) sidecar step=`"implemented"`, no review files → `("review", 1, plan_path)`; (5) sidecar step=`"review_failed:1"`, review-1.md present → `("implement", 2, plan_path)`; (6) slug mismatch: plan written as `01-slug.md`, caller passes seq `02` → resolves to `("plan_review", 1, canonical_01_path)`.

- [ ] **`_detect_test_milestone_step` unit tests** — `tests/test_main.py`. Same fixture setup as `_detect_milestone_step`. Mirror the implement-mode cases but use `test-runs/` directory and `test_run_failed:` sidecar prefix. Cases: (1) no plan → `("plan", 1, plan_path)`; (2) sidecar=`"plan_reviewed"`, clean git → `("implement", 1, plan_path)`; (3) sidecar=`"implemented"`, no test-run files → `("test_run", 1, plan_path)`; (4) sidecar=`"test_run_failed:1"`, test-1.txt present → `("implement", 2, plan_path)`.

## roadmap.py

- [ ] **`parse_roadmap` + roadmap helpers unit tests** — `tests/test_roadmap.py`. Import: `from orchestrator.roadmap import parse_roadmap, Milestone, _find_milestone_line, mark_done, mark_skipped`. Use `tmp_path` to write roadmap files. `parse_roadmap` cases: (1) mixed done/pending milestones → correct `done` flags; (2) `---STOP---` with milestones after → `breakpoint_hit=True`, `milestones_after_breakpoint` count correct; (3) `---STOP---` at end of file with nothing after → `breakpoint_hit=False`; (4) `##` heading assigns `section` to subsequent milestones; (5) malformed lines (missing `**`) skipped. `Milestone.slug` cases: (6) title with spaces, em dashes, mixed case → lowercase hyphen-slug, no leading/trailing hyphens; (7) title with numbers → digits preserved. `_find_milestone_line` cases: (8) unchecked line matching title → correct index; (9) checked line with same title → None (must be unchecked); (10) title absent → None. `mark_done` / `mark_skipped` cases: (11) `mark_done` flips `[ ]` → `[x]` and appends elapsed; (12) `mark_skipped` writes SKIPPED marker; (13) `mark_done` finds line by title even when `line_number` is stale.
