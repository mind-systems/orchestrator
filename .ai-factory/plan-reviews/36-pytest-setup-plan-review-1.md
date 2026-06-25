# Plan Review: pytest setup (36-pytest-setup.md)

**Plan Reviewed:** `.ai-factory/plans/36-pytest-setup.md`
**Risk Level:** 🔴 High — the plan's stated success condition is not achievable as written; the milestone would loop and never pass.

## Context Gates

- **ARCHITECTURE.md** — WARN (informational only). The folder-structure block shows `tests/` is not yet a tracked layer, which is expected for an infra scaffold. Adding a top-level `tests/` package does not violate any dependency rule (tests sit outside the `main → agents → roadmap` chain). No architectural conflict. Note: ARCHITECTURE.md's tree omits `config.py` and `notify.py` that exist in the repo — pre-existing drift, out of scope for this plan.
- **RULES.md** — WARN: file not present (`.ai-factory/RULES.md` missing). No explicit convention rules to enforce.
- **ROADMAP_TESTS.md** — Aligned. This plan maps to the `## Infra` → **pytest setup** milestone. However, that roadmap line itself carries the same incorrect premise (see Critical Issue #1), so "alignment" here means the plan faithfully inherited a wrong assumption.
- **skill-context** — `.ai-factory/skill-context/` not present; no project-specific review overrides to apply.

## Critical Issues

### 1. (BLOCKING) `uv run pytest --collect-only` exits **5**, not **0**, on an empty suite — the milestone can never pass

This is the core defect. The plan asserts in three places that the test command "must exit 0" / "Confirm it exits 0":
- line 12 Test Command: `uv run pytest --collect-only`
- line 19: "exit 0 ('no tests ran' is the success condition here)"
- lines 43–44: "Confirm it exits 0 and reports no tests collected"

pytest returns **`ExitCode.NO_TESTS_COLLECTED` (5)** whenever `session.testscollected == 0`, regardless of `--collect-only`. The relevant pytest logic is:

```python
config.hook.pytest_collection(session=session)
config.hook.pytest_runtestloop(session=session)
if session.testsfailed:
    return ExitCode.TESTS_FAILED      # 1
elif session.testscollected == 0:
    return ExitCode.NO_TESTS_COLLECTED  # 5
```

So an empty suite exits **5**, and the verification step (Task 3) will report failure, not success.

Why this is fatal for *this* milestone specifically: the `test` pipeline scores this milestone with `TestRunner.run()` (`orchestrator/agents.py:406`), which returns pass/fail strictly as `result.returncode == 0` (line 427). With exit code 5 the TestRunner returns `False` every time → the Implementer is re-invoked → it still can't make zero-test `--collect-only` exit 0 → the milestone loops until `max_iterations` is exhausted and stops with "TEST never passed". The plan as written is internally contradictory: it demands *both* "zero tests collected" *and* "exit 0", which pytest does not allow together.

**Pick one of these fixes and bake it into the plan:**

- **Option A (recommended — keeps zero tests, uses the conftest.py the plan already creates):** make `tests/conftest.py` non-empty with a session hook that remaps the empty-suite code to success:
  ```python
  # tests/conftest.py
  def pytest_sessionfinish(session, exitstatus):
      # NO_TESTS_COLLECTED (5) is the success condition for the empty scaffold.
      if exitstatus == 5:
          session.exitstatus = 0
  ```
  This contradicts the plan's current line 20 / Task 2 instruction that conftest.py is "intentionally empty," so update those statements too. Caveat to call out in the plan: this hook stays in place for later milestones and would silently turn a genuine "no tests collected" run into a pass — acceptable for the scaffold but worth a comment, and the subsequent milestones run `uv run pytest tests/ -v` which will collect real tests so the hook won't fire.

- **Option B (change the command, keep conftest empty):** since `TestRunner` runs the command with `shell=True` (agents.py:417), a compound command can normalize the exit code:
  ```
  ## Test Command
  `uv run pytest --collect-only -q; c=$?; [ $c -eq 0 -o $c -eq 5 ]`
  ```
  The extractor (`_extract_test_command`) returns the first non-heading line after `## Test Command`; this line is not backtick-balanced at both ends... — note: it IS wrapped in a single pair of backticks, so `.strip("`")` yields the inner shell expression cleanly. Verify the inner backticks/quoting survive extraction before relying on this.

- **Option C (add one trivial collectible test):** create `tests/test_smoke.py` with `def test_package_imports(): import orchestrator`. Collection becomes non-empty → exit 0 naturally. This contradicts the plan's "writes NO test functions" rule and the ROADMAP_TESTS infra description, so only choose it if you also relax those statements.

I recommend **Option A**: it preserves the milestone's intent ("empty, collectible suite"), reuses the `conftest.py` already in scope, and needs no shell trickery.

## Non-Blocking Issues / Recommendations

### 2. (WARN) The ROADMAP_TESTS.md milestone text propagates the same wrong premise
`ROADMAP_TESTS.md` line 7 says: "Verify `uv run pytest --collect-only` exits 0 with 'no tests ran'." The plan didn't invent the error — it inherited it from the roadmap. Whichever fix is chosen for the plan, update the roadmap line too so future re-planning of this milestone doesn't regenerate the same broken success condition.

### 3. (INFO) Hatchling wheel build with a new top-level `tests/` package — verified low risk
Adding `tests/__init__.py` creates a second top-level package alongside `orchestrator/`. With the root `pyproject.toml` using `build-backend = "hatchling.build"` and `name = "orchestrator"`, hatchling's auto-detection ships the package matching the project name (`orchestrator/`, which has `__init__.py`) and ignores `tests/`. So `uv add --dev pytest` (which re-resolves and re-syncs the editable install) should not raise "Unable to determine which files to ship." No action required, but if the implementer hits a hatchling packaging error during `uv add`, the fix is to pin `[tool.hatch.build.targets.wheel] packages = ["orchestrator"]`.

### 4. (INFO) `uv add --dev` target group
uv 0.10.11 writes dev deps to `[dependency-groups] dev` (PEP 735), not `[tool.uv.dev-dependencies]`. The plan's Task 1 says "Confirm `pytest` appears under the dev dependency group" — that phrasing is correct for this uv version. Just don't assert a specific table name in the plan beyond "dev dependency group."

### 5. (INFO) Import path correctness — confirmed
The plan's reasoning (lines 18) is right: there is a single `pyproject.toml` at the repo root (`/Users/max/projects/orchestrator/pyproject.toml`), the importable package `orchestrator` lives at `orchestrator/orchestrator/`, and it is installed editable. Placing `tests/` at the repo root keeps `from orchestrator.agents import ...` importable in later milestones. (Note: the project CLAUDE.md still shows `cd orchestrator && uv sync`, which is stale relative to the current single-root layout — not this plan's problem, but don't let it mislead the implementer into running `uv` from the wrong directory.)

## Positive Notes

- Correctly identifies the real project root and the editable-package layout, and justifies the `tests/` location with the downstream import requirement — the trickiest part of the scaffold, and it's right.
- Scopes the milestone tightly (deps + empty package + collection check) with no source-behavior testing — appropriate for an infra task.
- Provides a concrete `## Test Command` section in the format `TestRunner._extract_test_command` expects, so the `test`-mode pipeline can score it without manual wiring.
- Phasing (install/scaffold → verify) is clean and the file list is accurate.

## Verdict

The plan must not pass as-is: its success condition (`--collect-only` exits 0 on zero tests) is impossible, so the `test`-mode pipeline would loop to `max_iterations` and stop. Apply fix Option A (preferred) for Critical Issue #1, update the conftest "intentionally empty" statements accordingly, and align the ROADMAP_TESTS.md line (Issue #2). Re-review after those changes.
