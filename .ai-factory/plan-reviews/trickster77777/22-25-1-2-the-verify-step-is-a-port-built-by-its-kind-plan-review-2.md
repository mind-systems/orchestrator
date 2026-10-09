## Plan Review Summary

**Plan:** 25.1.2 — the verify step is a port, built by its kind
**Files Reviewed:** the plan; `orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, `tests/test_main.py`, `tests/conftest.py`, `pyproject.toml`, `docs/features/test-mode.md`, `docs/pipeline.md`, `CLAUDE.md`, `.ai-factory/ARCHITECTURE.md`, task spec `.ai-factory/specs/trickster77777/0060-the-verify-step-is-a-port-chosen-with-the-mode.md`, contract line 25.1.2 in `.ai-factory/roadmaps/trickster77777.md`, previous plan review (`…-plan-review-1.md`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture: OK.** The plan carries out ARCHITECTURE.md § What varies (Verify step). `VerifierProtocol` is the port, `PlannerReviewer` and `TestRunner` implement it, and `VerifyKind` holds "the factory that builds the implementation for a task". It also follows § The rule: once `mode.verify.step == "test_run"` and `mode.verify.step == "review"` are removed, the flow no longer branches on the mode. The direction of dependencies is unchanged: `agents.py` imports nothing new from `main.py`.
- **Rules: WARN (optional file missing).** There is no `.ai-factory/RULES.md`. `VerifierProtocol` has the `Protocol` suffix, as the global rule on interface naming requires.
- **Roadmap: OK.** Contract line 25.1.2 is the first `[ ]` after 25.1.1 `[x]`, so it is the next task in order. Its `Spec:` tag resolves to spec 0060, and the plan matches the spec point for point: the port signature; `PlannerReviewer.verify` delegating to `review`; `TestRunner.__init__(project_dir)`; `make_verifier` as the last field, with no default; `_review_verifier` and `_test_run_verifier`; `prev_out_path` for every mode; no comparison against a literal; no new test.

### Previous review follow-up

- Plan-review-1 issue 1 (the final grep also matched stale `__pycache__/*.pyc`) is **fixed**. The step "Verify nothing else references the old surface" now uses `--include='*.py' --include='*.md'`. Running the pattern against today's tree matches only `orchestrator/main.py` lines 228, 230–232 and 320, which are exactly the lines the plan replaces.

### Verification against the code

- `agents.py` has `from __future__ import annotations`, so the `Callable[[PlannerReviewer, Path], VerifierProtocol]` annotation is never evaluated, and the forward references are safe. A plain function stored in a `NamedTuple` field comes back unbound, so `mode.verify.make_verifier(planner_reviewer, project_dir)` passes exactly two arguments. `_test_run_verifier` looks up `TestRunner` only when it is called.
- `VerifyKind(...)` is built in only two places, the `REVIEW_VERIFY` and `TEST_RUN_VERIFY` instances, both with keyword arguments. The `IMPLEMENT_MODE._replace` and `TEST_MODE._replace` calls in `main.py` touch `Mode` fields only. A new last field with no default therefore breaks nothing.
- `main.py` uses `TestRunner` only on line 228, so removing it from the import is safe. No test monkeypatches `main_module.TestRunner`. The escalated-sidecar test patches only `PlannerReviewer`, `Implementer` and `PlanReviewer`, and it raises before the "Create agents" block, which is where the verifier gets built.
- The `TestRunner.run` body uses `output_path` and `project_dir` exactly where the plan says to rename them, including the early-return path that writes `ERROR: No '## Test Command'…`. The plan's mechanical rename covers all of them.
- Behaviour stays the same. The review kind receives the same `prev_out_path` it receives today. The test-run kind now receives it too and ignores it. The resume comparisons `step == mode.verify.step` and `step in ("implement", mode.verify.step)` are explicitly left alone.
- Baseline: `uv run pytest` gives **224 passed, no warnings**.

### Critical Issues

None.

### Issues

1. **Adding `TestRunner.__init__` puts a new `PytestCollectionWarning` into the suite, and the plan doesn't account for it.** `tests/test_agents.py` imports `TestRunner` into the test module's namespace. pytest tries to collect every `Test*` class there. Today `TestRunner` has no constructor and no `test_*` methods, so it is collected silently. Once the step **TestRunner implements the port** gives it `__init__(self, project_dir)`, pytest prints `PytestCollectionWarning: cannot collect test class 'TestRunner' because it has a __init__ constructor (from: tests/test_agents.py)` on every run. I reproduced this in isolation (pytest ≥ 9.1, same class shape): the run ends `1 passed, 1 warning`. The suite still passes, so the plan's "confirm the existing suite still passes" check does not catch it. But the clean baseline (`224 passed`, no warnings) becomes `224 passed, 1 warning`, and the spec's § What breaks on contact does not list that side effect. **Fix (stays inside `agents.py`, consistent with the spec):** in the same step, add a class attribute `__test__ = False` to `TestRunner`. This tells pytest the class is not a test class. Then extend the final step's check to "`uv run pytest` passes with no warnings".

### Positive Notes

- Every edit is given down to the exact signature, keyword placement and position in the module. The order of steps (port → implementations → factory → flow) matches the define-before-use constraints of the module.
- The plan says up front that the test-run kind now receives `prev_out_path`, and gives the reason this doesn't change behaviour.
- It keeps `_extract_test_command` a `@staticmethod` and names the class-level calls in `tests/test_agents.py` that depend on that.
- It protects the two resume comparisons against `mode.verify.step` from being "fixed" by mistake, and turns the no-literal acceptance into a grep someone can run.
