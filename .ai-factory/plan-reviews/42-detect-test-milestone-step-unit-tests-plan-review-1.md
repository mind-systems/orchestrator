## Plan Review Summary

**Plan:** `_detect_test_milestone_step` unit tests (milestone 42)
**Files Reviewed:** plan + `orchestrator/main.py` (lines 108-500), `tests/test_main.py`, `.ai-factory/ROADMAP_TESTS.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture (`.ai-factory/ARCHITECTURE.md`)**: present — no boundary/dependency conflict. Plan adds tests only, no production changes. OK.
- **Rules (`.ai-factory/RULES.md`)**: not present — gate skipped. WARN (optional file).
- **Roadmap linkage**: This is a `test`-mode milestone tracked in `ROADMAP_TESTS.md` (consistent with the existing `_has_signal` test entry). Test command `uv run pytest tests/test_main.py` matches the existing test file. OK.

### Verification Against the Codebase
Every grounded claim in the plan was checked against `main.py` and found correct:

- **Signature** (`main.py:430-432`): `_detect_test_milestone_step(project_dir, seq, slug, plan_path, plan_reviews_dir, test_runs_dir)` — confirmed, no `reviews_dir`. ✓
- **Sidecar validation** (`main.py:456-459`): called with `fail_prefix="test_run_failed:"`, `fail_suffix="-test-{n}.txt"`. `_validate_sidecar_step` (`main.py:145-152`) gates `test_run_failed:N` on `test_runs_dir / "{seq}-{slug}-test-{n}.txt"` → `01-slug-test-1.txt`. ✓
- **Sidecar dispatch**: `plan_reviewed → ("implement",1)` (`466-467`), `implemented → ("test_run",1)` (`468-469`), `test_run_failed:1 → ("implement",2)` (`470-472`). ✓
- **`plan_reviewed` gating**: requires a `plan-reviews/{seq}-{slug}-plan-review-*.md` ending in `PLAN_REVIEW_PASS` (`main.py:138-144`) — the plan correctly says to write that passing file. ✓
- **`implemented` and `test_run_failed:1` short-circuit before git** (`460-472`) — plan correctly states no git fixture needed for the Phase 1 cases. ✓
- **Heuristic done path**: passing plan-review (`475-480`) → dirty tree (`490`) → latest `test-runs/{seq}-{slug}-test-*.txt` ends with `TEST_PASS` (`493-498`) → `("done", 0)`. ✓
- **Dirty-tree technique**: an untracked file outside `.ai-factory/` (e.g. `tmp_path/src.py`) makes `git status --porcelain -- . :!.ai-factory` non-empty, satisfying the `not ... and not ...` guard at `main.py:490`. Correct — `:!.ai-factory` excludes the plan/review artifacts; the git fixture matches the existing clean-tree test. ✓
- **Import / fixture style**: mirrors existing `_dms_dirs` and the clean-tree git fixture in `test_main.py`. ✓

No missing steps, wrong path assumptions, API misuse, or architectural mistakes found. Test-only milestone, no migrations involved.

### Non-Blocking Observations
- **Branch coverage is partial (not a defect).** The function has ~12 distinct return branches; the plan pins 5 of them (no-plan, `plan_reviewed`, `implemented`, `test_run_failed:1`, done-via-`TEST_PASS`). Untested branches include: sidecar `planned`/`plan_review_failed:N`, missing-plan-review fall-through, non-passing plan-review, clean-tree `("implement",1)`, no-test-run-files `("test_run",1)`, and final `("implement", len+1)` on a non-passing latest test-run. The milestone's stated intent is "the five documented resume points," so this is a deliberate scope choice rather than an error — but if the goal is robust regression coverage of the resume logic, consider a follow-up adding the heuristic-tail cases (clean-tree and non-passing test-run are the highest-value gaps, since they mirror real interrupted-run states).
- **Note line 26 is slightly under-inclusive** ("Cases 2 and 4 ... short-circuit before git"). In Task 1 *all four* cases return before reaching git — case 1 returns at `main.py:452`, and the `plan_reviewed`/`implemented`/`test_run_failed` cases all short-circuit at `460-472`. Harmless wording; no action needed.

### Positive Notes
- Line-level grounding (`main.py:430-500`) is accurate throughout — the implementer can write tests directly from the notes without re-deriving behavior.
- Correctly distinguishes the sidecar-gated artifact filename (`-test-{n}.txt`) from the heuristic glob (`-test-*.txt`) and the `TEST_PASS` vs `PLAN_REVIEW_PASS` markers.
- Reuses established fixture conventions, keeping the new tests consistent with the existing suite.

The plan is solid and ready to implement.

PLAN_REVIEW_PASS
