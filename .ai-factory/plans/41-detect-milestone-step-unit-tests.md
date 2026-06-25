# Test Plan: `_detect_milestone_step` unit tests

## Context
`_detect_milestone_step` (`orchestrator/main.py:157`) inspects on-disk artifacts (plan file, JSON sidecar, plan-review/review files, git working-tree state) to decide where an interrupted milestone run should resume, returning `(step, counter, plan_path)`. These tests pin its branch logic against real files in `tmp_path`.

## Settings
- Testing: yes
- Logging: minimal
- Docs: no

## Test Command
`uv run pytest tests/test_main.py -k detect_milestone_step`

> Run from the repo root (`/Users/max/projects/orchestrator/`). The single `pyproject.toml` and the single `tests/` dir both live at the root; the inner `orchestrator/` is the package dir and has no `tests/`. Do **not** prefix `cd orchestrator` — `uv run` executes in the cwd, so that prefix makes pytest look for `orchestrator/tests/test_main.py` (does not exist) and exit 4, which `TestRunner.run()` treats as failure forever.

## Target Spec File
`tests/test_main.py`

## Naming requirement
Name every test function with the prefix `test_detect_milestone_step_*` so the `-k detect_milestone_step` filter collects them. (Existing tests use `test_validate_*` / `test_*_pattern_*`, which the filter deliberately excludes.)

## Tasks

### Phase 1: `_detect_milestone_step` — resume detection

Import under test: `from orchestrator.main import _detect_milestone_step`.

Key facts the implementer must encode in fixtures (all traceable to `main.py`):
- Signature: `_detect_milestone_step(project_dir, seq, slug, plan_path, plan_reviews_dir, reviews_dir)` → `(step, counter, plan_path)` (`main.py:157-160`).
- Sidecar file is `plan_path.with_suffix('.json')` — i.e. `plans/{seq}-{slug}.json` alongside the plan file (`agents.py:48`, read via `_read_sessions` at `main.py:192`). Write it as JSON, e.g. `{"step": "planned"}`. `_read_sessions` returns `{}` when the file is absent (`agents.py:49-50`), which skips the sidecar dispatch entirely.
- Use a stable `seq="01"`, `slug="slug"`; plan file at `tmp_path/.ai-factory/plans/01-slug.md`; `plan_reviews_dir=tmp_path/.ai-factory/plan-reviews`; `reviews_dir=tmp_path/.ai-factory/reviews`. Create parent dirs before writing.
- Plan-review file pattern: `{seq}-{slug}-plan-review-{n}.md`, passing marker = content ending with `PLAN_REVIEW_PASS` (`main.py:213-218`).
- Review file pattern: `{seq}-{slug}-review-{n}.md` (`main.py:234`).
- A shared helper that builds the `.ai-factory/{plans,plan-reviews,reviews}` dir tree and returns the relevant paths will keep the cases readable; the implementer chooses the exact shape.

- [x] **Task 1: Fresh start and sidecar-driven steps (no git repo needed)**
  Files: `tests/test_main.py`
  `project_dir=tmp_path` with no git repo is fine here — every case below returns before the git subprocess calls (`main.py:221-231`).
  Test cases:
  - `should return ("plan", 1, plan_path) when the plan file does not exist` (case 1 — `main.py:188-189`)
  - `should return ("plan_review", 1, plan_path) when sidecar step is "planned"` (case 2 — `main.py:198-199`; returns at 199 regardless of any plan-review files)
  - `should return ("review", 1, plan_path) when sidecar step is "implemented"` (case 4 — `main.py:205-206`)
  - `should return ("implement", 2, plan_path) when sidecar step is "review_failed:1" and reviews/01-slug-review-1.md is present` (case 5 — `main.py:207-209`, counter = n+1). The review file must exist, otherwise `_validate_sidecar_step` (`main.py:145-152`) clears the step and the flow falls through to a different branch.

- [x] **Task 2: Clean-working-tree branch (git fixture genuinely required)**
  Files: `tests/test_main.py`
  This targets the git-dependent branch at `main.py:221-231` (the most complex path), **not** the sidecar dispatch. To reach it: **omit the sidecar `step`** so `_read_sessions` → `{}` and the dispatch is skipped; provide a passing plan-review file so line 218 passes; keep the working tree clean.
  Setup:
  - Do **not** write a sidecar `.json` (or write one without a `"step"` key).
  - Write `plan-reviews/01-slug-plan-review-1.md` ending with `PLAN_REVIEW_PASS`.
  - `project_dir=tmp_path`, with a git repo: run `git init`, then `git -c user.email=t@t.com -c user.name=T commit --allow-empty -m init` in `tmp_path` (user config is required for the commit; not needed for diff/status). The `.ai-factory/` artifacts are the only files present and are excluded by `:!.ai-factory`, so both `git diff HEAD -- . :!.ai-factory` and `git status --porcelain -- . :!.ai-factory` return empty stdout — the "clean working tree" condition (`main.py:222-230`).
  Test cases:
  - `should return ("implement", 1, plan_path) when there is no sidecar step, a passing plan-review file is present, and the working tree is clean` (case 3 — `main.py:230-231`)

- [x] **Task 3: Canonical slug/seq resolution on mismatch**
  Files: `tests/test_main.py`
  Test cases:
  - `should resolve the canonical plan path to 01-slug.md and return ("plan_review", 1, that path) when the existing plan is plans/01-slug.md but the caller passes seq="02" and plan_path=plans/02-slug.md` (case 6 — `main.py:171-185` picks the lowest-numbered file matching `*-slug.md`; with no sidecar step and no plan-review files, flow falls through to `main.py:214-215`). Only create `plans/01-slug.md` on disk (do **not** create `02-slug.md` — `01` still wins, but omitting it keeps the fixture clean). Assert the returned `Path` equals the `01-slug.md` path, not the passed-in `02-slug.md`.

## Coverage note
This milestone intentionally scopes to cases 1–6. The remaining branches — failed plan-review → re-plan (`main.py:218-219`), no review files → review (`235-236`), failed review → re-implement (`239-240`), and the terminal `done` (`243`) — are out of scope and left untested here.
