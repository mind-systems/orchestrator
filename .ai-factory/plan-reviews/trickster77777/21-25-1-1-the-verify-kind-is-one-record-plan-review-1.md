## Plan Review Summary

**Plan:** 25.1.1 — the verify kind is one record
**Files targeted:** `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/resume.py`
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap (named roadmap `roadmaps/trickster77777.md`):** OK. The plan matches the 25.1.1 contract line, which is the first `[ ]` task under Phase 25. Its out-of-scope list matches the neighbouring tasks: the `_verify` closure and the `== "test_run"` / `== "review"` comparisons belong to 25.1.2, the hand-joined subdirectories to 25.2, and the `PLAN_REVIEW_PASS` / `endswith` readers to Phase 26.
- **Task spec (`specs/trickster77777/0062-the-verify-kind-is-one-record.md`):** OK. Every "What must be true after" clause has a matching plan step:
  - the record's field order, with no defaults;
  - both instances' values, which are identical to the spec table and to today's `IMPLEMENT_MODE` / `TEST_MODE`;
  - `verify` placed before `artifact_subdir`;
  - the `_detect_step` signature change, with `_validate_sidecar_step` unchanged;
  - the wrapper docstrings;
  - pass signals read from the kind in `PlannerReviewer.review` and `TestRunner.run`;
  - prompt files left as they are;
  - no new test.
- **Architecture (`ARCHITECTURE.md` § What varies, § Dependency rules):** OK. `VerifyKind` sits beside its implementations in `agents.py`, as § What varies requires. `main` → `agents` and `resume` → `agents` are both allowed directions, and `agents.py` imports neither `main` nor `resume`, so no cycle forms. The new constants are data, not step-selection logic, so the ❌ "Step-selection logic in `agents.py`" rule is not touched.
- **Rules (`.ai-factory/RULES.md`):** WARN. The file is not present, so there are no explicit conventions to check against.
- **Skill context (`.ai-factory/skill-context/aif-review/SKILL.md`):** not present.

### Verification against the codebase

- **`Mode` (`main.py`):** the nine fields the plan removes are exactly the verify fields that exist today. The resulting order `roadmap_relpath, header_label, planner_prompt_name, skip_message, verify, artifact_subdir` is valid, because only `artifact_subdir` has a default.
- **`_replace` calls:** both calls (in `_test_loop` and `_implement_loop`) touch only `roadmap_relpath`, `planner_prompt_name` and `artifact_subdir`. The plan is right that they need no change.
- **`process_task` field uses:** the plan's per-use list covers every reference: output dir, the `_detect_step` call, `TestRunner` construction, `impl_start`, the resume-mid-verify condition, the three `output_suffix.format` uses, the `== "review"` previous-review guard, the running header, the pass and fail labels, the sidecar fail tag, and the max-iterations message. The plan's grep currently matches 14 lines, which is all of them. The grep's BRE `\|` alternation works on this macOS grep, so a clean result is meaningful.
- **`_detect_step` (`resume.py`):** the plan lists every body use of the four loose parameters: the `_validate_sidecar_step` argument pair, both `return (verify_step, …)` lines, the `startswith(verify_fail_tag)` branch, the output glob, and the `endswith(pass_signal)` check. The docstring's `Steps:` line is covered as well.
- **Wrappers:** `_detect_task_step` / `_detect_test_task_step` keep their signatures. Their "Literals below mirror …" docstring lines are replaced as the spec asks.
- **`agents.py`:**
  - Both `PlannerReviewer.review` prompt sentences are already f-strings, so interpolating `{REVIEW_VERIFY.pass_signal}` renders identical text.
  - The module-level instances are referenced only inside method bodies, so their placement above `class PlannerReviewer` is safe.
  - `from __future__ import annotations` is compatible with `typing.NamedTuple` field annotations.
- **Tests:** no test builds a `Mode`, calls `_detect_step` directly, or reads a moved field. The baseline `uv run pytest` passes now (224 passed), which confirms the plan's verification step is meaningful.
- **Docs:** no file under `docs/`, `CLAUDE.md` or `README.md` names any moved field, `IMPLEMENT_MODE`/`TEST_MODE` or the new names, so `Docs: no` is correct.

### Critical Issues

None.

### Positive Notes

- Scope discipline is precise. The plan says explicitly which literal comparisons stay, and it names the later task (25.1.2 or Phase 26) that owns each one. This keeps the step behaviour-neutral and leaves 25.1.2 a clean seam.
- The import-graph smoke check (`from orchestrator.main import IMPLEMENT_MODE, TEST_MODE`) cheaply proves there is no cycle. The field-name grep proves the migration in `process_task` is complete.
- Moving the inline comments from `Mode` onto the matching `VerifyKind` fields keeps the placeholder documentation with the values it describes.

## Deferred observations
- Affects: `.ai-factory/ARCHITECTURE.md` (governing spec of Phase 25) — In § Dependency rules, the bullet "support modules import downward only" describes `resume`→`agents` with the parenthetical (`_read_sessions`). After this task `resume.py` also imports `VerifyKind`, `REVIEW_VERIFY` and `TEST_RUN_VERIFY` from `agents`. The direction is still allowed, as the task spec notes, but the parenthetical list of imported names becomes incomplete. The fix is a governing-spec edit outside this task's file boundary. The owner of ARCHITECTURE.md should either widen the parenthetical or drop the name list, so the rule states only the direction.

PLAN_REVIEW_PASS
