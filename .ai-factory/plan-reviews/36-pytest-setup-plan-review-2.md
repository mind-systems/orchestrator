# Plan Review: pytest setup (36-pytest-setup.md) — Round 2

**Plan Reviewed:** `.ai-factory/plans/36-pytest-setup.md`
**Risk Level:** 🟢 Low — the blocking defect from round 1 is fully resolved; the mechanism is empirically verified.

## Resolution of Round-1 Findings

Round 1 (🔴 High) raised one blocking issue: `uv run pytest --collect-only` exits **5** (`NO_TESTS_COLLECTED`) on an empty suite, so the `test`-mode pipeline (`TestRunner.run()` → `returncode == 0`) would loop until `max_iterations` and stop with "TEST never passed."

The revised plan adopts **Option A** end-to-end:
- The "Critical premise correction" section (lines 6–9) names the exact pytest exit code (5) and why it is fatal for *this* milestone given `TestRunner` scores strictly on `returncode == 0`.
- Task 2 (lines 43–50) now creates a **non-empty** `tests/conftest.py` with the `pytest_sessionfinish` remap hook.
- Every "intentionally empty conftest" statement from the prior draft is gone; line 26 explicitly states `conftest.py` is **not** empty and contains only the remap hook.
- Task 3 (lines 54–58) correctly attributes the exit-0 result to the hook.

This is the recommended fix and it is applied consistently across the whole file. No contradictions remain.

## Verification Performed

I empirically reproduced the scaffold in a throwaway directory (`tests/__init__.py` empty + `tests/conftest.py` with the exact hook from the plan) and ran `python -m pytest --collect-only` with **pytest 9.1.1**:

```
collected 0 items
========================= no tests collected in 0.00s ==========================
EXIT=0
```

Confirmed:
- `pytest_sessionfinish` fires even under `--collect-only` (it runs in `wrap_session`'s `finally`, unconditionally), and mutating `session.exitstatus = 0` propagates to the process exit code.
- A `conftest.py` living in a sub-package (`tests/`) is loaded during collection of an empty suite — pytest descends into `tests/` and imports it before session finish, so the hook registers and fires.
- Net process exit code is **0**, which is exactly what `TestRunner.run()` needs to mark the milestone passed.

I also confirmed against the live codebase:
- `TestRunner.run()` returns `result.returncode == 0` (`orchestrator/agents.py:427`) and runs the command with `shell=True` in the project dir — matches the plan's assumptions.
- `_extract_test_command` (`agents.py:435–452`) returns the first backtick-wrapped line after `## Test Command`, stripping backticks. The plan's `` `uv run pytest --collect-only` `` extracts cleanly to `uv run pytest --collect-only`.
- Repo layout: single root `pyproject.toml` (`name = "orchestrator"`, `build-backend = "hatchling.build"`), importable package at `orchestrator/orchestrator/`, no `tests/` dir yet. The plan's placement of `tests/` at the repo root (lines 20, 24) is correct for keeping `from orchestrator.agents import ...` importable in later milestones.

## Context Gates

- **ARCHITECTURE.md** — WARN (informational). A top-level `tests/` package sits outside the `main → agents → roadmap` dependency chain and violates no boundary rule. Pre-existing drift in ARCHITECTURE.md's tree (omits `config.py`/`notify.py`) is out of scope.
- **RULES.md** — WARN: `.ai-factory/RULES.md` not present; no explicit convention rules to enforce.
- **ROADMAP.md / ROADMAP_TESTS.md** — Aligned. Maps to `## Infra → pytest setup`. The roadmap line says the command "exits 0 with 'no tests ran'"; round 1 flagged this as a propagated wrong premise (WARN). With Option A applied, the conftest hook makes that statement **literally true**, so no roadmap edit is required to make the milestone pass. (Optional nicety: a one-line note in ROADMAP_TESTS.md that exit-0 depends on the conftest hook would help a future re-plan, but this is non-blocking and not needed for correctness.)
- **skill-context** — `.ai-factory/skill-context/aif-review/` not present; no project-specific review overrides to apply.

## Non-Blocking Observations

1. **(INFO) Hatchling wheel build** — Adding `tests/__init__.py` introduces a second top-level package. Hatchling auto-detects the package matching the project name (`orchestrator/`) and ignores `tests/`, so `uv add --dev pytest` should not raise "Unable to determine which files to ship." The plan already documents the `[tool.hatch.build.targets.wheel] packages = ["orchestrator"]` fallback (line 27) if it surfaces. Good defensive note.
2. **(INFO) Dev dependency group** — uv writes `pytest` to `[dependency-groups] dev` (PEP 735). Task 1's phrasing ("dev dependency group") is correct and does not over-assert a table name.
3. **(INFO) Hook longevity** — The remap hook persists into later milestones. Once `tests/test_*.py` files exist, collection is non-empty, exit code is 0 naturally, and the hook never fires. The only residual behavior is that a genuine future "0 tests collected" run would be masked as a pass — acceptable for this scaffold and already acknowledged in the plan (line 9). Worth keeping in mind, not worth changing.

## Positive Notes

- Cleanly absorbed the round-1 fix without leaving any contradictory leftover statements.
- The "read first" premise-correction section makes the non-obvious pytest exit-code behavior impossible for the implementer to miss.
- Test Command section is in the exact format `_extract_test_command` expects, so the `test`-mode pipeline scores it with no manual wiring.
- File list and phasing (install/scaffold → verify) are accurate and minimal.

## Verdict

The blocking issue is resolved and the mechanism is verified end-to-end against real pytest. The plan is correct, internally consistent, and matches the codebase. Ready to implement.

PLAN_REVIEW_PASS
