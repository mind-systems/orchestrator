## Plan Review Summary

**Plan:** Express the milestone pipeline once (implement / test)
**Files Reviewed:** plan + `orchestrator/main.py`, `tests/test_main.py`, spec `06-unify-milestone-pipeline.md`, `.ai-factory/ARCHITECTURE.md`, `ROADMAP.md`, prior review `-plan-review-1.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (OK): `ARCHITECTURE.md` names `process_milestone()` in the module map. Task 3 keeps `process_milestone` as the single entry point and Task 4 deletes `process_test_milestone` (which is not named in the map), so no doc drift. Intra-`main.py` dedup — no boundary/dependency change.
- **Rules**: `.ai-factory/RULES.md` absent — gate skipped.
- **Roadmap**: Milestone line present in `ROADMAP.md:39`; its `Spec:` note (`specs/06-unify-milestone-pipeline.md`) followed to leaf. The plan faithfully carries the spec's divergence table, invariants (implement-only `prev_review_path`, task-05 `HaltError`/`PipelineStopError` split, byte-for-byte artifact/sidecar/print strings), and the "pytest stays green, zero assertion changes" safety net. Dependency on task 05 is satisfied — the exception split is already live in `main.py` (`HaltError` at 359, `PipelineStopError` at 337/352/392). Alignment good.
- **Skill-context**: `.ai-factory/skill-context/aif-review/SKILL.md` absent — no project overrides.

### Prior-review resolution (review 1)
Review 1 raised one critical issue and two minor notes. All are resolved in this revision:
- **Critical (mode default):** Task 3 now mandates `mode` **defaults to `IMPLEMENT_MODE`** and spells out exactly why — the four-positional-arg call at `tests/test_main.py:789` (`process_milestone(tmp_path, _MilestoneStub(), 1, config)`) must keep resolving to implement mode and hit the `impl_start(4) > max_iterations(3)` → `HaltError` path. Verified against the source: the test seeds `step: review_failed:3` + a `review-3.md` + a passing plan-review, so the detector returns `("implement", 4, …)`, and with the default the `isinstance(exc.value, HaltError)` assertion stays green. Correct fix, chosen from review 1's two options.
- **Minor (anchor):** Task 1 now cites `374/638` for the verify-running header (`>>> REVIEWING` / `>>> RUNNING TESTS`), matching source. Fixed.
- **Minor (`_replace` vs dataclass):** Task 1 now commits to `NamedTuple` explicitly *so that* `_replace` is available for Task 4's `_implement_loop` override. Internally consistent.

### Verification performed
- **Every line anchor in Task 1 matches source:** header `269`/`535`, skip-message `314`/`580`, verify-running header `374`/`638`, pass line `386`/`645`, fail line `389`/`648`, max-iterations raise `392-395`/`651-654`.
- **Task 2 ranges correct:** `_detect_milestone_step` `165-251`, `_detect_test_milestone_step` `448-518`, `_validate_sidecar_step` `116-162` (already shared/parametrized).
- **Detector wrapper signatures preserved:** `tests/test_main.py` calls both detectors positionally with 6 args (e.g. `:249-250`, `:484`). Task 2 keeps both names as thin wrappers with their current exact signatures — the tested public behaviour is intact, no assertion touched.
- **Task 3 ranges correct:** `process_milestone` `254-405`, `process_test_milestone` `521-664`, implement-only prev-output guard `377-381`. The `verify(iteration, out_path, prev_out_path)` closure built after agent construction is the right shape; `TestRunner()` correctly scoped to test mode only.
- **Detector-tail equivalence holds:** implement's `not review_files → review / not endswith REVIEW_PASS → implement / else done` and test's `not test_run_files → test_run / endswith TEST_PASS → done / else implement` are the same logic phrased inversely and collapse cleanly to `not files → verify_step / endswith pass_signal → done / else implement(len+1)`.
- **Task 4 caller sweep:** the only two references to `process_test_milestone` are its `def` (`521`) and the `_test_loop` lambda (`729`); Task 4 removes both. The old positional `planner_prompt_name`/`roadmap_filename` call at `741` is replaced by `mode`. Protocol untouched (artifact names, PASS signals, sidecar fields all byte-for-byte identical), so the mirrored skills protocol needs no change — consistent with the "touch `main.py` only" constraint.

### Positive Notes
- The revision addresses review 1 by editing the plan's own reasoning, not by hand-waving — the `mode`-default rationale is tied to the concrete failing assertion and the detector's actual return value.
- Staging (Task 1 introduces the descriptor with nothing wired) keeps each diff reviewable; dependencies between tasks are declared.
- The verify-output path formula `output_dir / f"{seq}-{slug}{mode.output_suffix.format(n=iteration)}"` reproduces both current filenames exactly. Note for the implementer: the **implementer-feedback** path (the previous iteration's output fed into `implementer.implement`, `main.py:369`/`633`) is the same tail at `n=iteration-1` — reuse `mode.output_suffix.format(n=iteration-1)` there so it stays byte-for-byte identical; the plan's byte-for-byte-filenames invariant already governs it.

### Deferred observations
_None._

The plan is complete, internally consistent, faithful to the spec, and preserves every stated invariant. The prior critical issue is correctly resolved.

PLAN_REVIEW_PASS
