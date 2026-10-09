## Plan Review Summary

**Plan:** 25.1.2 — the verify step is a port, built by its kind
**Files Reviewed:** the plan; `orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, `docs/features/test-mode.md`, `docs/pipeline.md`, `.ai-factory/ARCHITECTURE.md`, the task spec `.ai-factory/specs/trickster77777/0060-the-verify-step-is-a-port-chosen-with-the-mode.md`, contract line 25.1.2 in `.ai-factory/roadmaps/trickster77777.md`, and plan reviews 1 and 2
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture: OK.** ARCHITECTURE.md § What varies (Verify step) names the port `VerifierProtocol`. Its two implementations are `PlannerReviewer` and `TestRunner`, and `VerifyKind` holds "the factory that builds the implementation for a task". The plan delivers exactly that. With both `mode.verify.step == "<literal>"` branches gone, the flow no longer asks which mode it is in, which satisfies § The rule. `agents.py` gets no new import from `main.py`, so dependencies still point the same way.
- **Rules: WARN (optional file missing).** There is no `.ai-factory/RULES.md`. `VerifierProtocol` ends in `Protocol`, so the name declares its kind as the global naming rule requires.
- **Roadmap: OK.** 25.1.1 is `[x]` and 25.1.2 is the next `[ ]`. Its `Spec:` tag resolves to spec 0060, and the plan matches the spec's § What must be true after on every point. It covers the port signature, `PlannerReviewer.verify` delegating to `review`, and `TestRunner.__init__(project_dir)`. It adds `make_verifier` as the last field, with no default, backed by `_review_verifier` and `_test_run_verifier`. It passes `prev_out_path` for every mode, keeps every comparison against a literal out of `process_task`, and adds no test.

### Previous review follow-up

- **Plan-review-1 (the stale `.pyc` grep match): fixed.** The final grep now uses `--include='*.py' --include='*.md'`. I ran it against today's tree. It matches only `orchestrator/main.py`: the `test_runner` construction, the `_verify` closure, and the `_verify(...)` call in the loop. The plan replaces all of these lines.
- **Plan-review-2 (`PytestCollectionWarning` once `TestRunner` gains `__init__`): fixed.** The plan adds `__test__ = False` to `TestRunner` and makes the final check "passes with no warnings". I tested this in isolation on the project's pytest 9.1.1. A test module imports a class named `TestRunner` that has `__test__ = False` and an `__init__`, and pytest reports `1 passed` with no warning.

### Verification against the code

- `agents.py` starts with `from __future__ import annotations`, so Python never evaluates `Callable[[PlannerReviewer, Path], VerifierProtocol]`. Both forward references are safe. `typing` currently imports only `NamedTuple`, and the plan widens that import to `Callable, NamedTuple, Protocol`.
- `VerifyKind(...)` is constructed only in `REVIEW_VERIFY` and `TEST_RUN_VERIFY`, both with keyword arguments. That makes a new last field with no default safe. The plan puts `_review_verifier` and `_test_run_verifier` before those instances, which is required. `_test_run_verifier` looks up `TestRunner` only when it is called.
- A plain function stored in a `NamedTuple` field comes back unbound. So `mode.verify.make_verifier(planner_reviewer, project_dir)` passes exactly two arguments.
- The `TestRunner.run` body uses `output_path` in three places (the early-return error write, `mkdir`, and the final write) and `project_dir` in one (`cwd=`). The plan's mechanical rename covers all of them.
- `TestRunner` appears in `main.py` only in the import and in the line being removed. No test monkeypatches `main_module.TestRunner`. `tests/test_agents.py` uses only the `_extract_test_command` staticmethod, and the plan keeps that unchanged.
- The verifier is built inside the "Create agents" block, which runs after the `escalated`/`done` early returns. The escalated-sidecar test therefore still holds.
- The plan leaves the resume comparisons (`step in ("implement", mode.verify.step)`, `step == mode.verify.step`) alone. The acceptance grep `'mode.verify.step =='` matches only the two literal comparisons the plan removes.
- The change is behaviour-neutral. The review kind receives the same `prev_out_path` it receives today. The test-run kind now receives it too and ignores it.
- `docs/features/test-mode.md` already says `TestRunner.verify()`, and `docs/pipeline.md` names only the class, so no doc changes are needed.
- Baseline today: `uv run pytest` reports **224 passed**, no warnings.

### Critical Issues

None.

### Issues

None.

### Positive Notes

- Every edit is specified down to the signature, the keyword placement and the position in the module. The step order (port → implementations → factory → flow) follows the module's define-before-use constraints.
- The plan states the one new value flow up front (`prev_out_path` reaching the test-run kind) and explains why it changes nothing.
- It records why `__test__ = False` is there and why `_extract_test_command` stays a staticmethod, so the implementer cannot drop either one by accident.
- The acceptance checks are greps that can be run, and they are scoped tightly enough that stale bytecode cannot match.

PLAN_REVIEW_PASS
