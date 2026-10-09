## Plan Review Summary

**Plan:** 25.1.2 — the verify step is a port, built by its kind
**Files Reviewed:** `orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, `tests/test_main.py`, `docs/features/test-mode.md`, `docs/pipeline.md`, `CLAUDE.md`, `.ai-factory/ARCHITECTURE.md`, the task spec `.ai-factory/specs/trickster77777/0060-the-verify-step-is-a-port-chosen-with-the-mode.md`, the contract line 25.1.2 in `.ai-factory/roadmaps/trickster77777.md`
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture — OK.** The plan carries out ARCHITECTURE.md § What varies (Verify step): `VerifierProtocol` is the port, `PlannerReviewer` and `TestRunner` implement it, and `VerifyKind` holds the factory. It also follows § The rule: the flow no longer branches on the mode. Dependency direction is unchanged, because `agents.py` gains no import from `main.py`.
- **Rules — WARN (missing optional file).** There is no `.ai-factory/RULES.md`. The name `VerifierProtocol` uses the `Protocol` suffix, which meets the global rule that interface names declare their kind.
- **Roadmap — OK.** Line 25.1.2 in `.ai-factory/roadmaps/trickster77777.md` matches the plan's heading. Its `Spec:` tag resolves to spec 0060, and the plan matches that spec point for point: the port signature, `PlannerReviewer.verify` delegating to `review`, the `TestRunner.__init__(project_dir)`, the last field with no default, `_review_verifier` / `_test_run_verifier`, `prev_out_path` for every mode, no comparison against a literal, and no test added. 25.1.1 is `[x]`, so the plan starts from the right point.

### Verification against the code

- `agents.py` has `from __future__ import annotations`, so `Callable[[PlannerReviewer, Path], VerifierProtocol]` in the `VerifyKind` field is a string annotation. `NamedTuple` does not evaluate it, which makes the forward references to `PlannerReviewer` and `VerifierProtocol` safe, as the plan says.
- A function stored in a `NamedTuple` field comes back unbound through `_tuplegetter`. So `mode.verify.make_verifier(planner_reviewer, project_dir)` calls the module function with exactly the two arguments.
- `_test_run_verifier` refers to `TestRunner`, which is defined later in the module. The name is looked up when the function is called, so this is safe.
- `IMPLEMENT_MODE._replace(...)` / `TEST_MODE._replace(...)` in `main.py` replace only `Mode` fields, so the extra `VerifyKind` field does not affect them. Nothing else constructs `VerifyKind` positionally: `grep` finds only the two module instances.
- `tests/test_agents.py` uses `TestRunner` only through the `_extract_test_command` staticmethod. Nothing in `tests/` calls `TestRunner()` or `.run(`.
- `test_process_task_escalated_sidecar_raises_without_constructing_agents` monkeypatches the agent constructors and raises before the "Create agents" block. The verifier is built inside that block, so the test still holds.
- The plan checks behaviour neutrality correctly. Today `prev_out_path` is only computed for the review kind. Afterwards the test-run kind receives it too, and `TestRunner.verify` ignores it. Resume uses `step == mode.verify.step` and `step in ("implement", mode.verify.step)`, which compare against the kind's own value rather than a literal, and the plan leaves both untouched.
- `docs/features/test-mode.md` already says `TestRunner.verify()`, so no documentation change is needed.

### Critical Issues

None.

### Issues

1. **The final "no remaining references" grep gives a false positive because it also searches stale bytecode.** The step **Verify nothing else references the old surface** runs `grep -rn "TestRunner()\|\.run(plan_path\|_verify(\|test_runner" orchestrator tests docs` and says "It must find no remaining references". `orchestrator/__pycache__/main.cpython-313.pyc` is compiled from today's `main.py`, so it contains `test_runner` and `_verify`. Running this pattern against the tree now already prints `Binary file orchestrator/__pycache__/main.cpython-313.pyc matches`. The plan runs the grep *before* `uv run pytest`, so the `.pyc` is still stale when the grep runs, and the acceptance check fails as written even when the source edit is correct. **Fix:** restrict the grep to source and docs, e.g. `grep -rn --include='*.py' --include='*.md' "TestRunner()\|\.run(plan_path\|_verify(\|test_runner" orchestrator tests docs`, or add `-I` to skip binary files.

### Positive Notes

- The plan states every edit at the level of exact signatures and exact keyword placement, and the dependency order between tasks (port → implementations → factory → flow) matches the define-before-use constraints in the module.
- The plan says up front that the test-run kind now gets `prev_out_path` and explains why that does not change behaviour.
- It keeps `_extract_test_command` a staticmethod and gives the reason (the class-level calls in `tests/test_agents.py`).
- It protects the resume comparisons from being "fixed" by mistake.
