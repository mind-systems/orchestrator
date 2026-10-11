## Plan Review Summary

**Plan:** 26.2 — every reader recognizes a signal through `_has_signal`
**Files targeted:** `orchestrator/pipeline.py`, `orchestrator/resume.py`, `tests/test_main.py`
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture:** OK. `.ai-factory/ARCHITECTURE.md` places `pipeline.py` and `resume.py` in "the flow", with the dependency running `pipeline` → `resume`. Adding `_has_signal` to their existing `from .protocol import …` lines adds no new module edge, because both already import from `protocol`.
- **Rules:** WARN (non-blocking). `.ai-factory/RULES.md` does not exist, so there was nothing to check.
- **Roadmap:** OK. The plan matches the open contract line `26.2` in `.ai-factory/roadmaps/trickster77777.md`, which sits directly above `---STOP---`, the seam. `26.1` is done, and the tree confirms its result: `PLAN_REVIEW_PASS` is defined in `protocol.py` and imported by `agents`, `pipeline` and `resume`.
- **Spec walk:** The plan matches `.ai-factory/specs/trickster77777/0076-every-reader-recognizes-a-signal-one-way.md` point by point:
  - the three readers, all four check sites, the imports and the docstring change;
  - exactly two `_detect_step` tests, with expected results `implement` and `done`;
  - no test for the guard and no doc change.

  The governing spec, `docs/pipeline.md` § Completion signals, already states the last-five-lines reading, so leaving the docs alone is correct.
- **Skill context:** `.ai-factory/skill-context/aif-review/SKILL.md` does not exist.

### Verification against the codebase

- `_has_signal(text, signal)` in `orchestrator/protocol.py` checks `any(line.strip() == signal for line in text.splitlines()[-5:])`. It strips each line itself, so the plan is right to pass the raw `read_text()` without `.strip()`. `PlannerReviewer.review` and `PlanReviewer.review_plan` in `agents.py` call it the same way.
- `pipeline.py` currently imports `from .protocol import PLAN_REVIEW_PASS, _read_sessions, _write_session`. The guard under `# Safety guard: ensure a passing plan review exists before implementing` uses `.strip().endswith(PLAN_REVIEW_PASS)`, exactly as the plan quotes it. The proposed import order matches the existing style in `agents.py`: uppercase names first, then the underscore names alphabetically.
- `resume.py` currently imports `from .protocol import PLAN_REVIEW_PASS, _read_sessions`. The three `endswith` sites are in:
  - `_validate_sidecar_step`'s `plan_reviewed` branch;
  - `_detect_step` step 4;
  - `_detect_step` step 7, which uses `verify.pass_signal`.

  The docstring bullet the plan quotes is word-for-word what is in the file. The plan's closing check holds: after the change, `pipeline.py` and `resume.py` contain no other `endswith`.
- Test helpers `_dms_dirs`, `_detect_task_step` (which calls `REVIEW_VERIFY`) and `_init_dirty_git_repo`, the constants `DMS_SEQ`/`DMS_SLUG`, and both anchor tests all exist under the names the plan uses. The plan's claims about today's results are correct:
  - **Plan review with a stray line:** step 4 reads it as failed and returns `("plan", 2, …)`.
  - **Review with a stray line:** step 7 misses it and returns `("implement", len(output_files) + 1 = 2, …)`.

  So both new tests fail before the fix and pass after it.
- In the clean-tree test, the plan file is untracked after `git init` plus the empty commit. `_plan_is_stale` therefore returns False and the plan is adopted, as in the test it mirrors.
- **Existing fixtures:** every plan-review, review and test-run fixture in `tests/test_main.py` puts the signal on its own final line (`"…\n\nPLAN_REVIEW_PASS"`, `"…\nREVIEW_PASS"`, `"…\nTEST_PASS"`). The failing fixtures carry no signal line. `TestRunner.verify` appends `\n{TEST_RUN_VERIFY.pass_signal}` as the last line. Every existing resume and pipeline test keeps its current result, as the spec's "What breaks on contact" says.

### Critical Issues

None.

### Positive Notes

- The plan holds a strict scope. It adds only the two tests the spec names, explains why the guard gets no test (it fails loudly) and leaves `_validate_sidecar_step` without new tests, as the test philosophy requires.
- It quotes each change site by its comment or branch name instead of a line number, so the work order survives any edits above those sites.
- The closing `grep -n "endswith"` check is a cheap, concrete way to confirm the reader migration is complete.

PLAN_REVIEW_PASS
