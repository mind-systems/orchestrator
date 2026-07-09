## Plan Review Summary

**Plan:** Express the milestone pipeline once (implement / test)
**Files Reviewed:** plan + `orchestrator/main.py`, `tests/test_main.py`, spec `06-unify-milestone-pipeline.md`, `.ai-factory/ARCHITECTURE.md`, `ROADMAP.md`
**Risk Level:** 🟡 Medium

### Context Gates
- **Architecture** (WARN → clear): `ARCHITECTURE.md:21` names `process_milestone()` in the module map. The plan preserves the `process_milestone` name (Task 3 keeps it as the single entry point), so no doc drift. No boundary/dependency change — this is an intra-`main.py` dedup. OK.
- **Rules**: `.ai-factory/RULES.md` absent — gate skipped.
- **Roadmap**: Milestone line present in `ROADMAP.md` and its `Spec:` note (`specs/06-unify-milestone-pipeline.md`) both followed. The plan matches the spec faithfully — divergence table, invariants (implement-only `prev_review_path`, `HaltError`/`PipelineStopError` split from task 05, byte-for-byte artifact/sidecar/print strings), and the tests-green requirement are all carried through. Dependency on task 05 is satisfied (the exception split is already live in `main.py`; `2ab853e` landed the detector-matrix tests). Alignment good.

### Critical Issues

**1. The new required `mode` parameter breaks `test_process_milestone_resume_past_max_iterations_raises_halt_error` — contradicting the plan's own "pytest stays green, zero assertion changes" invariant.**

Task 3 specifies the signature `process_milestone(project_dir, milestone, milestone_index, config, mode, phase_session_id=None)` with `mode` as a **required positional** 5th argument (no default). But `tests/test_main.py:789` calls it with four positional args and no mode:

```python
process_milestone(tmp_path, _MilestoneStub(), 1, config)
```

Today this resolves via the current defaults (`planner_prompt_name="planner"`, `roadmap_filename="ROADMAP.md"`), runs the detector (sidecar `review_failed:3` → `implement` counter 4), hits `impl_start=4 > max_iterations=3`, and raises `HaltError` — which is exactly what the test asserts (`isinstance(exc.value, HaltError)`). After the refactor the same call raises `TypeError: process_milestone() missing 1 required positional argument: 'mode'`; `pytest.raises(Exception)` catches it, but the `isinstance(..., HaltError)` assertion then **fails**. `uv run pytest` goes red.

The plan carefully enumerates test-compatibility for the two detector wrappers (Task 2) but never mentions this `process_milestone` call site, and the imports at `test_main.py:14-20` / call at `:789` are the ones affected.

Fix — pick one and state it in the plan:
- **Preferred (keeps the test untouched):** give the parameter a default — `mode: Mode = IMPLEMENT_MODE`. `IMPLEMENT_MODE` is a module-level constant (Task 1), so this is clean and the existing 4-arg call keeps resolving to implement mode exactly as today.
- **Alternative:** update the test call in the same commit to `process_milestone(tmp_path, _MilestoneStub(), 1, config, IMPLEMENT_MODE)`. This is Class-A drift (a changed call, not a weakened assertion) and is explicitly sanctioned by the spec, but the plan must call it out, and it requires adding `IMPLEMENT_MODE` to the test's import list.

Either is acceptable; leaving it unaddressed is not, because the milestone's whole safety net is "the suite stays green."

### Positive Notes
- The divergence inventory is complete and line-anchored; I verified each cited literal (`269/535` header, `314/580` skip, `386/645` pass, `389/648` fail, `392-395/651-654` raise) matches the source.
- The detector-tail equivalence claim is correct: implement's `not review_files → review / not endswith PASS → implement / else done` and test's `not test_run_files → test_run / endswith PASS → done / else implement` are the same logic phrased inversely, and collapse cleanly to `not files → verify_step` / `endswith pass_signal → done` / `else implement(len+1)`.
- Keeping `_detect_milestone_step` / `_detect_test_milestone_step` as thin wrappers with their exact 6-arg signatures correctly preserves the positional test calls (`test_main.py:249, 484, …`).
- The implement-only `prev_out_path` guard (`main.py:377-381`) and the `TestRunner()`-only-in-test-mode instruction are both correctly scoped; the `verify` closure built after agent construction is the right shape for the two runtime divergences.
- Staging the work so Task 1 introduces the descriptor without wiring keeps the diff reviewable — good sequencing.

### Minor
- Task 1 cites `main.py:376/640` as the anchor for the verify-running header, but the `>>> REVIEWING` / `>>> RUNNING TESTS` prints are at `374/638` (376/640 are the output-path lines). Cosmetic — the intended strings are unambiguous — but worth correcting so the implementer copies from the right line.
- Task 4 suggests `IMPLEMENT_MODE._replace(...)`, which only exists if `Mode` is a `NamedTuple`; if the `@dataclass(frozen=True)` option from Task 1 is chosen, the implementer must use `dataclasses.replace` instead. The plan's "(or rebuild)" already leaves room, so this is just a heads-up, not a defect.

## Deferred observations
_None._

Address critical issue 1 (and ideally the two minor notes) and the plan is ready to implement.
