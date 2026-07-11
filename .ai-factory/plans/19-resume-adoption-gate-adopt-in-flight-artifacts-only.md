# Plan: Resume adoption gate — adopt in-flight artifacts only

## Context
`_detect_step`'s canonical-plan scan adopts the lowest-numbered `*-{slug}.md` plan unconditionally, so a recurring milestone title (same slug) matches a long-completed, committed plan and its `done` sidecar → `mark_done` + commit with zero work. This milestone gates candidate adoption on git state: tracked+clean plans are stale and skipped; only in-flight (untracked/modified/staged-but-uncommitted) plans are adoptable.

## Settings
- Testing: yes (milestone explicitly requires four gate tests + green specs-08 matrix)
- Logging: minimal
- Docs: yes (one sentence in `docs/how-it-works.md` resume section)

## Tasks

### Phase 1: Gate implementation

- [x] **Task 1: Add git-state staleness gate to the candidate scan**
  Files: `orchestrator/resume.py`
  In `_detect_step` (currently `resume.py:73-89`), keep the existing behavior of resolving the canonical seq/plan_path from slug-matching files, but insert a staleness gate before adoption. Add a small module-level pure helper, e.g. `_plan_is_stale(project_dir: Path, plan_file: Path) -> bool`, that runs `subprocess.run(["git", "status", "--porcelain", "--", str(plan_file)], cwd=project_dir, capture_output=True, text=True)` and returns `True` **only** when the call succeeds (`returncode == 0`) **and** `stdout.strip()` is empty (tracked + clean). Any other case — non-empty porcelain (untracked `??`, modified, or staged), non-zero return code (not a git repo), or an exception such as `FileNotFoundError` (git missing) — returns `False` (fail open toward adoption / re-planning, never toward `done`). Wrap the subprocess call in `try/except` so a raised error maps to `False`.

  Rewrite the candidate loop to iterate slug matches in ascending numeric order (digit-prefixed only, mirroring the existing `parts[0].isdigit()` guard), and adopt the **first (lowest-numbered) candidate for which `_plan_is_stale(...)` is `False`** (the in-flight survivor). If every digit-prefixed candidate is stale (tracked+clean), leave the computed `plan_path`/`seq` untouched — the fresh-plan path (`_next_number`'s seq), which then falls to step 1 (`plan_path.exists()` is `False` for a new seq → returns `("plan", 1, plan_path)`). One subprocess call per digit-prefixed candidate; slug matches are few.

  Do **not** touch `_validate_sidecar_step`, the sidecar step→(step, counter) dispatch table (`resume.py:101-114`), or the downstream heuristic (steps 3-7). The gate only decides which plan file is adopted before that machinery runs.

### Phase 2: Tests

- [x] **Task 2: Pin the gate over tmp git repos** (depends on Task 1)
  Files: `tests/test_main.py`
  Add gate tests alongside the existing `_detect_milestone_step` suite, reusing `_dms_dirs(tmp_path)` and the `git init` + `git -c user.email=... -c user.name=... commit` pattern from `_init_dirty_git_repo` / the clean-tree test (`test_main.py:233-243, 356-375`). Cover the four cases from the spec:
  - **(a) committed-skip:** init repo, write `plans/01-slug.md` with a sidecar `{"step": "done"}` (or a passing review artifact so the heuristic would return `done`), `git add -A` + commit so the plan is tracked+clean → `_detect_milestone_step` must **not** adopt it; assert the returned step is `plan`/fresh (not `done`) and the returned path is not the stale committed plan.
  - **(b) untracked-adopt:** plan file present but untracked (no commit) → adopted, resumes per today's behavior (assert non-`plan`/expected resume step, path == the plan).
  - **(c) staged-adopt:** plan file `git add`-ed but not committed → adopted (assert same as untracked case).
  - **(d) survivor-over-lowest:** two slug matches — lower seq committed+clean, higher seq in-flight (untracked or staged) → the **higher** one is adopted (survivor rule, not lowest-overall); assert the returned path/seq is the higher candidate.
  Follow the assertion style of the existing detector tests (`step`, `counter`, `returned_path`). Choose sidecar/artifact contents so each test isolates the gate decision.

- [x] **Task 3: Confirm the specs-08 matrix stays green** (depends on Task 1, Task 2)
  Files: `tests/test_main.py` (verification only)
  Run `uv run pytest` and confirm the existing `_detect_milestone_step` / `_detect_test_milestone_step` matrix passes unchanged — those fixtures use untracked files, which the gate adopts, so current assertions hold. No fixture edits expected; if any assertion breaks, the gate over-reached (skipping an in-flight plan) — fix Task 1 rather than the fixtures.

### Phase 3: Docs

- [x] **Task 4: Document the tracked-artifact assumption** (depends on Task 1)
  Files: `docs/how-it-works.md`
  Add one sentence to the resume section (`## Resume после прерывания`, near `resume.py`'s canonical-plan description around lines 23-25). Match the doc's existing language (Russian). State that plan adoption on resume leans on the artifact protocol — tracked+clean plans belong to completed milestones and are skipped, only uncommitted (in-flight) plans are resumed — and that a developer hand-committing a half-done milestone's artifacts degrades to re-planning (never to false completion).
