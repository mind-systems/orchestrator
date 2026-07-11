## Plan Review Summary

**Plan:** Per-roadmap artifact subdirectories — users never share a number axis
**Target files reviewed:** `orchestrator/main.py`, `orchestrator/resume.py`, `tests/test_main.py`, `docs/how-it-works.md`, `CLAUDE.md`, spec `13-artifact-subdirs.md`, ROADMAP line 53, `ARCHITECTURE.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture (`.ai-factory/ARCHITECTURE.md`)** — OK. All code changes stay in `main.py` (the orchestration layer: `_artifact_subdir` pure helper, `Mode` field, dir construction, loop setups). `resume.py` is explicitly untouched. No layering violation — step/dir logic belongs in `main.py`, consistent with the existing `_resolve_roadmap_relpath`/`_tests_sibling` helpers.
- **Rules (`.ai-factory/RULES.md`)** — WARN: file absent (optional). No violation.
- **Roadmap** — OK. Milestone under review is ROADMAP.md line 53, which names `Spec: .ai-factory/specs/13-artifact-subdirs.md`. The plan's tasks map 1:1 onto spec §Change.1–5 and the roadmap contract line. Dependency on task 12 (roadmap relpath resolution) is already merged — `_resolve_roadmap_relpath` and named-roadmap support exist in `main.py`.
- **Governing spec chain** — followed to leaf (`13-artifact-subdirs.md` → cited code lines in `main.py`/`resume.py`). Line references verified against ground truth.

### Verification of key claims against ground truth
- `_tests_sibling` is at `main.py:157-162` ✓; `Mode` NamedTuple at `24-38` ✓; `IMPLEMENT_MODE`/`TEST_MODE` literals at `41-71` use **keyword** args ✓; `process_milestone` dir construction at `190-195` ✓; `_detect_step` call at `204` ✓; `_run_dynamic_loop` at `348-399` with `plans_dir` at `350-351` and `_next_number(plans_dir)` at `386` ✓; `_test_loop`/`_implement_loop` `_replace` setups at `410`/`424` ✓; `CLAUDE.md:72` is exactly the output-directories line ✓.
- **NamedTuple default ordering** — correctly reasoned. No existing `Mode` field carries a default, so appending `artifact_subdir: str | None = None` as the last field is valid, and the keyword-based `IMPLEMENT_MODE`/`TEST_MODE` literals remain unchanged with the field defaulting to `None`.
- **Byte-stable default** — holds. `_artifact_subdir` maps both `"ROADMAP.md"` and `"ROADMAP_TESTS.md"` → `None`, so `process_milestone`, `_run_dynamic_loop`'s `plans_dir`, and every artifact path are identical to today for the default pair. The direct `process_milestone(...)` test (`test_process_milestone_resume_past_max_iterations_raises_halt_error`) uses default `IMPLEMENT_MODE` → `artifact_subdir=None` → flat paths, so it stays green.
- **Numbering consistency** — `_run_dynamic_loop` computes `i = _next_number(plans_dir)` and `process_milestone` rebuilds the same subdir'd `plans_dir` (Task 2); both count in the same directory, so the milestone index and `_detect_step`'s canonical-seq glob (`plan_path.parent`) agree. A fresh subdir starts at `01`, matching spec §Change.3.
- **Test/implement sibling split** — `_tests_sibling("roadmaps/kg-wmservice.md")` → `"roadmaps/kg-wmservice-tests.md"` → `_artifact_subdir` → `"kg-wmservice-tests"`, a sibling of the implement subdir `"kg-wmservice"`. Correct per spec §Change.3 (separate number axes, no filename contact).
- **`Path(relpath).stem`** — yields `"kg-wmservice"` for `roadmaps/kg-wmservice.md` and `"ROADMAP.watch"` for `ROADMAP.watch.md`, matching the spec's worked examples.
- **Sidecar/commit** — the JSON sidecar (`plan_path.with_suffix(".json")`) and `git add -A` naturally follow the plan into its subdir; no extra handling needed.
- **Docs language** — Task 5 correctly specifies Russian edits to `how-it-works.md` (matching the file) and touches the sidecar sentence at line 23 plus the "Файловый протокол" paragraph, and the `CLAUDE.md:72` file-protocol line. Skills-repo mirrors (`orchestrator-artifacts`, `roadmap-prune`) are correctly left out as separate skills-roadmap tasks per spec §Guards.

### Critical Issues
None.

### Positive Notes
- Line references are precise and were confirmed against the current source — no drift.
- The plan correctly identifies the one non-obvious threading hazard (`_run_dynamic_loop` builds its own `plans_dir` for `_next_number`) and addresses it in Task 3, preventing an inconsistent number axis between the loop and `process_milestone`.
- Migration is a genuine non-issue here (task-12 named-roadmap support is new, so no pre-existing named flat artifacts; the default pair is unchanged), and the spec §Guards explicitly waives it — the plan's silence on migration is correct, not an omission.
- Task boundaries and commit plan are clean, dependencies are stated, and the test task pins exactly the silent-failure surface (`_artifact_subdir` key mapping) plus a dirs-in/dispatch-out resume check.

PLAN_REVIEW_PASS
