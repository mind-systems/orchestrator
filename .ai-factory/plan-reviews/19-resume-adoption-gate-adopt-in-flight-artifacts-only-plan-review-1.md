## Plan Review Summary

**Plan:** Resume adoption gate — adopt in-flight artifacts only
**Files Reviewed:** plan + `orchestrator/resume.py`, `orchestrator/main.py`, `tests/test_main.py`, `docs/how-it-works.md`, spec `14-resume-adoption-gate.md`, ROADMAP line
**Risk Level:** 🟢 Low

### Context Gates
- **Roadmap alignment (WARN → OK):** The plan implements ROADMAP line 57 (milestone 19) faithfully — tracked+clean → stale/skip, adopt lowest in-flight survivor, none → fresh, git-status errors fail open toward re-planning. No linkage gap.
- **Spec alignment (OK):** Matches `.ai-factory/specs/14-resume-adoption-gate.md` clause-for-clause: the gate, the three surviving resume paths, the fail-open guard, dispatch-table untouched, four tests, specs-08 stays green, one Russian sentence in docs.
- **Architecture/Rules gates:** No `.ai-factory/ARCHITECTURE.md` boundary or `RULES.md` violation — change is confined to `_detect_step`'s candidate scan plus a pure module-level helper. No protocol change (directory layout, PASS signals, sidecar fields, review-section format all unchanged), so no `orchestrator-artifacts` skills-repo mirror update is required — the gate merely *enforces* the already-documented "tracked ⟺ completed / uncommitted ⟺ in-flight" contract. Correctly omitted from the plan.

### Critical Issues
None. Verified against ground truth:

- **`_next_number` citation is accurate and load-bearing.** The seq passed to `_detect_step` is `_next_number(plans_dir)` (`main.py:402` → `seq = f"{milestone_index:02d}"`, `main.py:210`). Because `_next_number` returns `max(existing) + 1`, the caller-passed `plan_path` for a recurring milestone is always numbered *above* every on-disk plan. So the "all candidates stale → leave `plan_path`/`seq` untouched → `plan_path.exists()` is False → `('plan', 1, …)`" reasoning holds in production, not just in principle — the fresh path can never collide with the committed stale plan. Design is sound.
- **Staged-survivor path is real.** `git add -A` runs before every verify pass (`main.py:329`), staging the plan `.md`; a crash after review-PASS but before `mark_done`+commit leaves the plan staged → `git status --porcelain -- <plan>` non-empty → `_plan_is_stale` False → adopted → detector returns `done` → completion path finishes. Preserved exactly. (The spec/plan cite `main.py:245` for this `git add -A`; the actual line is `329` — a harmless citation drift, no effect on the implementation.)
- **`.ai-factory/` is tracked, not ignored** (step-5's `:!.ai-factory` exclusion only makes sense on tracked paths, and artifacts are committed via `git add -A` + `_git_commit`). So `git status --porcelain -- <plan>` returns empty *only* for committed-clean plans, never for an ignored-but-present file — the gate cannot misread an in-flight plan as stale. No hidden failure mode.
- **Fail-open direction is correct.** `_plan_is_stale` returns `True` only on `returncode == 0` *and* empty stdout; every other case (non-empty porcelain, non-zero return, `FileNotFoundError`, any exception) → `False` = adoptable → never manufactures `done`. Matches the spec guard.
- **Numeric (not lexicographic) ascending order is specified**, avoiding the 3-digit-seq ordering trap (`"100"` < `"20"` lexicographically). Good.
- **Dispatch table and `_validate_sidecar_step` left untouched**, as the spec's guard demands.

### Positive Notes
- Clean separation: a pure `_plan_is_stale(project_dir, plan_file) -> bool` helper keeps the git-coupling isolated and independently reasoned; the candidate loop only decides *which* file to adopt before the existing machinery runs.
- Test surface is exactly the silent-failure grade this milestone targets (wrong `done`, no crash) — the four cases (committed-skip / untracked-adopt / staged-adopt / survivor-over-lowest) pin every branch of the gate, and Task 3's "if the matrix breaks, fix Task 1 not the fixtures" instruction correctly encodes the invariant that in-flight (untracked) fixtures must stay adopted.
- For Task 2 case (a), the assertion "returned path is not the stale committed plan" combined with the existing `test_detect_milestone_step_canonical_path_resolution` pattern (committed `01-slug.md`, caller passes `02-slug.md`) already steers the implementer to pass a seq *above* the committed plan — the only configuration that faithfully mirrors `_next_number` and exercises the fresh-plan branch. The plan is implementable as written.

PLAN_REVIEW_PASS
