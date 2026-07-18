# Plan: Rename `milestone` code identifiers to `task`

## Context
A pure, behavior-neutral symbol rename: the Python surface (`orchestrator/*.py` + `tests/*.py`) still names the processed roadmap unit `milestone`, but the reserved word is `task`. Rename every identifier and in-code docstring/comment `milestone`→`task`, symbol-aware, while leaving Phase-6-owned user-facing string literals, alert tokens, `print` wording, and config byte-for-byte. No on-disk format changes, so resume stays byte-stable and the existing suite must stay green.

**Assumption (boundary decision):** `agents.py:304` holds a *prompt* string literal `"Create an implementation plan for this milestone:"` that is neither a Phase-6 operator-facing string, an alert token, `print` wording, config, nor a Phase-7 `.md` prompt body — no later phase claims it, and the spec's Verify grep must return **only** Phase-6 literals plus the three alert-token test names. It is therefore renamed here (`milestone`→`task`) as the roadmap unit it names. The hard "leave string literals byte-for-byte" constraint protects the *Phase-6* set (tokens / "Milestone done" / print wording / config), not this prompt prose.

### Shared reference — LEAVE UNCHANGED (Phase 6 owns; do NOT rename the string/token contents)
Rename any *identifier* embedded on these lines, but keep the quoted text/token byte-for-byte:
- `notify.py`: `_FAIL_ALERTS = {"milestone-fail"}` and the `"milestone"` / `"milestone-fail"` tokens.
- `main.py`: line 51 `skip_message="…(milestone may already be done)…"`; the `"Milestone done: {…}"` notify text and its `"milestone"` token (lines 241, 359); the `print(">>> Milestone done …")` lines (243, 362); the `"No passing plan review found for milestone …"` exception text (311); `"All milestones are done!"` (378); the pending-count `print` text "milestones" (382, 384); `"All milestones done: …"` (394); the `"Milestone '…' checkbox … same milestone forever"` exception text (401–402); the argparse `--help` strings "…milestones" (484–485); the `"milestone-fail"` token (505).
- `runtime.py`: the sigint `print` string "…current milestone finishes…" (23); the run-summary text "milestones done" (39).
- `test_notify.py`: **entire file unchanged** — alert tokens and the two alert-token test names (`test_milestone_fail_alert_prefixed_red`, `test_milestone_alert_prefixed_green`) with their docstrings/assertions.
- `test_config.py`: the `"milestone-fail"` token in the override + assertion (111, 115) — unchanged.
- `test_main.py`: `test_cli_pipeline_stop_error_routes_to_milestone_fail` (848) — name, docstring, and `"milestone-fail"` assertion (849, 853) unchanged.
- `test_runtime.py`: docstrings and assertions that *quote* the still-legacy "milestones done" output (17, 24, 30, 35) and the "…current milestone finishes." print assertion (167) — unchanged.

## Settings
- Testing: no (existing suite renamed in lockstep; no new tests)
- Logging: minimal
- Docs: no

## Tasks

### Phase 1: Source identifier rename

- [x] **Task 1: Rename `Milestone`/`milestones`/`_find_milestone_line` in `roadmap.py`**
  Files: `orchestrator/roadmap.py`
  Rename the `@dataclass Milestone` → `Task` (leave the `slug` property and its concept untouched — out of scope). In `ParseResult`: `milestones: list[Task]` and `milestones_after_breakpoint` → `tasks` / `tasks_after_breakpoint`. Rename the `parse_roadmap` locals `milestones` / `milestones_after_breakpoint` → `tasks` / `tasks_after_breakpoint` and the `Milestone(...)` constructor call → `Task(...)`. Rename `_find_milestone_line` → `_find_task_line` and its `milestone` param → `task` (used in `mark_done`, `mark_skipped`, whose `milestone` params also → `task`). Rename the docstrings/comments that say "milestone" (lines 38–39, 74, 87, 104) → "task".

- [x] **Task 2: Rename `_detect_milestone_step`/`_detect_test_milestone_step` in `resume.py`**
  Files: `orchestrator/resume.py`
  Rename `_detect_milestone_step` → `_detect_task_step` and `_detect_test_milestone_step` → `_detect_test_task_step` (thin wrappers over `_detect_step`; only these two are consumed by tests, `main.py` calls `_detect_step` directly). Rename the comments/docstrings that say "completed milestone" (lines 61, 103) → "completed task".

- [x] **Task 3: Rename `milestones_done` → `tasks_done` in `state.py` and `runtime.py`**
  Files: `orchestrator/state.py`, `orchestrator/runtime.py`
  `state.py`: `milestones_done: int = 0` → `tasks_done: int = 0`. `runtime.py:39`: `state.milestones_done` → `state.tasks_done` inside the run-summary f-string — keep the literal text "milestones done" and the sigint print (line 23) byte-for-byte (Phase 6).

- [x] **Task 4: Rename identifiers in `main.py`** (depends on Tasks 1, 3)
  Note: `Mode.header_label` literals `"MILESTONE"` (line 44) / `"TEST MILESTONE"` (line 60) are Phase-6-owned user-facing prose (roadmap 6.1) — left byte-for-byte, per review-1 finding.
  Files: `orchestrator/main.py`
  Rename `process_milestone` → `process_task` (def + both `lambda … process_milestone(…)` call sites, lines 433, 448) and its params `milestone` → `task`, `milestone_index` → `task_index`. Rename `_git_commit`'s `milestone_title` param → `task_title` (line 177 + uses at 187, 189) **and its docstring `"…after a completed milestone."` (line 178) → "…completed task."**. Rename the locals `milestone_start` → `task_start`, `milestone` → `task`; rename every `milestone.slug`/`.title`/`.description`/`.line_number`/`.section` → `task.…`, `result.milestones` → `result.tasks`, `result.milestones_after_breakpoint` → `result.tasks_after_breakpoint`, and `state.milestones_done` → `state.tasks_done` (lines 239, 357, 458, 471). Rename the module docstring (line 1) and the `_git_commit` docstring (178) plus the `single milestone` / `each milestone` / `pending milestones` / `implement milestones` docstrings (199, 367, 423, 439, 454) → "task"/"tasks". **Per the LEAVE UNCHANGED list above:** on lines 241, 311, 359, 382, 384, 401 rename only the embedded identifier and keep the surrounding string/token text (line 384's `result.milestones` → `result.tasks`, keeping "pending milestones … total"); leave lines 51, 243, 362, 378, 394, 402(text), 484–485, 505 strings byte-for-byte.

- [x] **Task 5: Rename `plan()` params + prompt prose in `agents.py`** (depends on Task 4's caller signature staying compatible)
  Files: `orchestrator/agents.py`
  Rename `PlannerReviewer.plan(self, milestone_title, milestone_description, …)` → `task_title`, `task_description` (def line 292 + f-string uses at 306–307). Rename the docstrings "not a milestone failure" (70) → "not a task failure" and "Plans and reviews milestones…" (274) → "…tasks…". Rename the prompt prose `"Create an implementation plan for this milestone:"` (304) → `"…for this task:"` (see Context assumption). `main.py`'s `planner_reviewer.plan(task.title, task.description, …)` calls are positional, so they carry over from Task 4.

- [x] **Task 6: Rename comments in `notify.py`**
  Files: `orchestrator/notify.py`
  Rename the two comments (lines 14, 17) "report a milestone failure" / "not a milestone failure" → "…task failure". Leave `_FAIL_ALERTS = {"milestone-fail"}` and every token literal byte-for-byte (Phase 6).

### Phase 2: Test rename in lockstep

- [x] **Task 7: Rename `test_roadmap.py`** (depends on Task 1)
  Files: `tests/test_roadmap.py`
  Update the import `from orchestrator.roadmap import _find_milestone_line, …, Milestone` → `_find_task_line`, `Task`; rename every `Milestone(...)` construction → `Task(...)` and `_find_milestone_line(...)` → `_find_task_line(...)`; `result.milestones` → `result.tasks`, `result.milestones_after_breakpoint` → `result.tasks_after_breakpoint`. Rename the test-function definitions `test_find_milestone_line_unchecked_match` / `test_find_milestone_line_already_checked_returns_none` / `test_find_milestone_line_no_match_returns_none` (lines 182, 193, 202) → the `test_find_task_line_*` form (distinct symbols, not `_find_milestone_line(...)` call sites — rename explicitly, symbol-aware). Rename the test function `test_parse_roadmap_milestones_after_breakpoint_count` → `…tasks_after_breakpoint_count` and the module docstring/comments (lines 1, 21, 50, 70, 90, 107, 119–120, 143, 153, 178, 183, 251, 267, 298) "milestone" → "task". Rename the **test-fixture and asserted title strings** that contain "milestone" (e.g. "Done milestone", "Pending milestone", "Real milestone", "Milestone A/B", "Early/Later milestone", bare "Milestone") → the "task" form on both the fixture line and its matching assertion — these are arbitrary test data, not Phase-6 literals, and must rename together to stay green and keep the Verify grep clean.

- [x] **Task 8: Rename `test_main.py`** (depends on Tasks 2, 4)
  Files: `tests/test_main.py`
  Update imports: `process_milestone` → `process_task`, `_detect_milestone_step` → `_detect_task_step`, `_detect_test_milestone_step` → `_detect_test_task_step` (lines 21, 24, 25) and every call site. Rename all `test_detect_milestone_step_*`, `test_detect_test_milestone_step_*`, and `test_process_milestone_*` function names and their comments (`# _detect_milestone_step tests`, etc.) → the "task" form. Rename `_MilestoneStub` → `_TaskStub` (916, 923) and its `title = "Some milestone"` fixture string → "Some task"; rename the module docstring (line 1) and comments (212, 465, 587, 1114) → "task". **Leave** `test_cli_pipeline_stop_error_routes_to_milestone_fail` (848) — its name, docstring, and `"milestone-fail"` assertion (849, 853) stay byte-for-byte (Phase 6 alert token).

- [x] **Task 9: Rename identifiers in `test_runtime.py`** (depends on Task 3)
  Files: `tests/test_runtime.py`
  Rename `state.milestones_done` → `state.tasks_done` everywhere (lines 18, 21, 26, 31, 34, 37). Leave the docstrings and assertions that quote the still-legacy runtime output ("… N milestones done", "Ran for unknown · 0 milestones done", "…current milestone finishes.") byte-for-byte — they test Phase-6-owned strings and must keep matching the unchanged `runtime.py` output.

- [x] **Task 10: Rename the roadmap-unit comment in `test_agents.py`**
  Files: `tests/test_agents.py`
  Rename the in-code comment `# Task 5: RED case -- semver ordering (fixed in milestone 2.2)` (line 260) → "…(fixed in task 2.2)". This is the only "milestone" occurrence in the file — an in-code comment naming the roadmap unit, in Phase 5's scope and spanned by the Verify grep; nothing else in `test_agents.py` changes.

### Phase 3: Verify

- [x] **Task 11: Verify green suite and clean grep** (depends on Tasks 1–10)
  Files: (none — verification only)
  Run `uv run pytest` — the full suite must be green (any failure means a missed reference, not a needed test change). Run `grep -rnE '[A-Za-z_]*[Mm]ilestone[A-Za-z_]*' orchestrator/*.py tests/*.py` and confirm every residual hit is either (a) a Phase-6 user-facing string literal / alert token / `print` wording / quoted-output test assertion from the LEAVE UNCHANGED list, or (b) the three alert-token test names (`test_milestone_fail_alert_prefixed_red`, `test_milestone_alert_prefixed_green`, `test_cli_pipeline_stop_error_routes_to_milestone_fail`). No identifier, docstring, or comment may survive.

## Commit Plan
- **Single commit** (after tasks 1–11): "Rename milestone code identifiers to task"

  This milestone is one atomic, behavior-neutral rename spanning defining modules and their test consumers. No proper sub-slice leaves the suite green — renaming `roadmap.py`'s `Milestone` without `test_roadmap.py` (or `process_milestone` without `test_main.py`) breaks import/collection — so the whole rename lands in a single commit rather than staged checkpoints.
