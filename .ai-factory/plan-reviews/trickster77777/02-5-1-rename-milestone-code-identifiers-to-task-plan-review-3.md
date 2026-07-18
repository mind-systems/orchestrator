# Plan Review: Rename `milestone` code identifiers to `task` (5.1) — round 3

**Plan:** `plans/trickster77777/02-5-1-rename-milestone-code-identifiers-to-task.md`
**Spec:** `.ai-factory/specs/trickster77777/24-code-identifiers-milestone-to-task.md`
**Roadmap:** `.ai-factory/roadmaps/trickster77777.md` → Phase 5 → 5.1
**Files Reviewed:** plan + full grep sweep of `orchestrator/*.py` and `tests/*.py`
**Risk Level:** 🟢 Low — both round-2 findings are closed; a full line-by-line reconciliation of every `[Mm]ilestone` hit against the plan leaves no residual unaccounted for.

## Round-2 status
- **Finding 1 (`main.py:384` misfiled as byte-for-byte)** — CLOSED. Task 4 now places line 384 in the *rename-identifier* group ("line 384's `result.milestones` → `result.tasks`, keeping 'pending milestones … total'"), alongside 241/311/359/382/401. The runtime `AttributeError` and Verify-grep failure are both averted.
- **Finding 2 (`test_find_milestone_line_*` function names omitted)** — CLOSED. Task 7 now explicitly renames the three definitions at `test_roadmap.py:182, 193, 202` → the `test_find_task_line_*` form, symbol-aware.

## Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md` present): OK. A behavior-neutral symbol rename crosses no module boundary or dependency direction.
- **Rules** (`.ai-factory/RULES.md`): absent — WARN (optional file, nothing to check).
- **Roadmap alignment**: OK. Maps cleanly to Phase 5 → 5.1. The `agents.py:304` prompt-prose boundary is now positively confirmed against ground truth: Phase 7 (7.1) scopes only the `orchestrator/prompts/*.md` bodies (`planner.md`, `test-planner.md`, `reviewer.md`), and Phase 6 (6.1) scopes only alert tokens / "Milestone done" text / print wording / `--help` / config. The inline f-string at `agents.py:304` is claimed by neither, so renaming it here is required for Task 11's Verify grep to come clean.

## Verification performed
I reconciled every hit of `grep -rnE '[A-Za-z_]*[Mm]ilestone[A-Za-z_]*' orchestrator/*.py tests/*.py` against the plan's task set. Each identifier/docstring/comment occurrence maps to an explicit rename directive, and each surviving string/token maps to an explicit LEAVE UNCHANGED entry:

- **`roadmap.py`** — dataclass (13), `ParseResult` fields (30, 32), parse locals (43, 45, 55, 67, 69, 70), `_find_milestone_line` + params (73, 81, 86, 89, 91, 103, 106, 108), docstrings/comments (38–39, 74, 87, 104): all covered by Task 1.
- **`resume.py`** — `_detect_milestone_step`/`_detect_test_milestone_step` (169, 184) + comments (61, 103): Task 2.
- **`state.py` / `runtime.py`** — `milestones_done` (state 15; runtime 39 identifier, 23/39-text left): Task 3.
- **`main.py`** — every `.slug/.title/.description/.line_number/.section`, `result.milestones(_after_breakpoint)`, `milestone_start/index`, `process_milestone`, `_git_commit` param+docstring (178), `state.milestones_done`, module docstring, and the mixed-line split (241/311/359/382/384/401 rename-identifier vs 51/243/362/378/394/402-text/484–485/505 leave): Task 4. Pure-identifier lines with no co-located string (376, 381, 392, 409, 410, 415) fall under the general "rename every …" rules — correct, since there is no string to protect.
- **`agents.py`** — `plan()` params (292, 306–307), docstrings (70, 274), prompt prose (304): Task 5.
- **`notify.py`** — comments (14, 17); `_FAIL_ALERTS` token left (15): Task 6.
- **`test_roadmap.py`** — import (5), constructions/calls, `result.milestones*`, the `test_find_milestone_line_*` and `test_parse_roadmap_milestones_after_breakpoint_count` defs, the enumerated docstrings/comments (1, 21, 50, 70, 90, 107, 119–120, 143, 153, 178, 183, 251, 267, 298), and every fixture/assertion title string ("Done/Pending/Real milestone", "Milestone A/B", "Early/Later milestone", bare "Milestone"): Task 7.
- **`test_main.py`** — imports (21, 24, 25), all `test_detect_milestone_step_*` / `test_detect_test_milestone_step_*` / `test_process_milestone_*` names + call sites + comments (212, 465, 587, 1114), `_MilestoneStub` + its `"Some milestone"` fixture (916, 918, 923); the alert-token name at 848/849/853 left: Task 8.
- **`test_runtime.py`** — `state.milestones_done` (18, 21, 26, 31, 34, 37) renamed; quoted-output docstrings/assertions (17, 24, 30, 35, 167) left: Task 9.
- **`test_agents.py`** — the single comment (260): Task 10.
- **`test_notify.py` / `test_config.py`** — entire alert-token surface left byte-for-byte: LEAVE UNCHANGED list.

Every residual `[Mm]ilestone` after the rename falls into exactly Task 11's allowed set — (a) a Phase-6 string/token/print/quoted-output on the LEAVE UNCHANGED list, or (b) the three alert-token test names. No identifier, docstring, or comment survives.

## Positive Notes
- Line references remain exact against the current code — spot-re-verified the round-2 fixes (`main.py:384`, `test_roadmap.py:182/193/202`) and the mixed-line splits (401/402, 382/384).
- The symbol-aware discipline is applied consistently: distinct symbols (test-function definitions, `_MilestoneStub`) are renamed explicitly rather than folded into call-site sweeps, matching the spec's "not a blind replace" mandate.
- The fixture-title-string reasoning (arbitrary test data must rename with its assertion to stay green *and* keep the grep clean) is correctly distinguished from Phase-6 user-facing literals — and applied symmetrically to `test_main.py:918` (`"Some milestone"`) and the `test_roadmap.py` titles.
- The single-commit rationale holds: no sub-slice keeps the suite green (a renamed symbol without its test consumer breaks import/collection).

## Verdict
Both round-2 findings are resolved, and an exhaustive reconciliation of the grep sweep against the plan finds no unaccounted-for identifier, docstring, or comment, and no misfiled string. The `agents.py:304` boundary is positively confirmed against Phase 6 and Phase 7 scopes. The plan is complete, line-accurate, internally consistent, and satisfies its own Task 11 acceptance. Ready to implement.

PLAN_REVIEW_PASS
