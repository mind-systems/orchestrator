## Code Review Summary

**Files Reviewed:** 3 (`orchestrator/pipeline.py`, `orchestrator/resume.py`, `tests/test_main.py`)
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture:** OK. `pipeline` and `resume` now also import `_has_signal` from `protocol` (Vocabulary layer), so imports still point down. `resume` imports only from `ports` and `protocol`, never from `agents`.
- **Rules:** OK. `.ai-factory/RULES.md` does not exist, and there is no skill-context file for review.
- **Roadmap:** OK. This matches the open task 26.2 in `.ai-factory/roadmaps/trickster77777.md` and its spec `0076-every-reader-recognizes-a-signal-one-way.md`. Governing spec `docs/pipeline.md` § Completion signals already states the last-five-lines reading, and the code now conforms to it. No doc change is needed.

### Critical Issues
None.

Checked:
- All three call sites the spec names now use `_has_signal(text, signal)` on the full `read_text()`: the `pipeline.py` safety guard, the `plan_reviewed` branch of `_validate_sidecar_step`, and steps 4 and 7 of `_detect_step`. Each still uses the signal it used before (`PLAN_REVIEW_PASS` or `verify.pass_signal`). Dropping `.strip()` is correct because `_has_signal` strips each line itself and `splitlines()[-5:]` ignores a trailing newline.
- No `.endswith(` signal checks are left in `orchestrator/` (`grep` finds only an unrelated backtick check in `agents.py`).
- The `_validate_sidecar_step` docstring now states the exact-line, last-five-lines reading.
- The guard keeps its `not _plan_review_files or ...` short-circuit and its `PipelineStopError` message.
- Both new tests sit next to their sibling `_detect_step` tests and reuse `_dms_dirs`, `_detect_task_step` and `_init_dirty_git_repo`. Each puts a non-signal line after the signal. On the old `endswith` code they would have resolved to `("plan", 2, …)` and `("implement", 2, …)`. Now they assert `("implement", 1, …)` and `("done", 0, …)`, as the spec requires.
- Existing fixtures end with the signal as their last line, so they resolve as before. Existing test docstrings that say "ends with …" still describe their fixtures accurately.
- `uv run pytest`: 229 passed.

### Positive Notes
- The change is small and does exactly what the task asks: three checks, one docstring and two tests, with no extra scope.
- After this change, `_has_signal` is the only way the codebase recognizes a signal, which matches the spec's one-way recognition.
- The test docstrings say why each test exists: a resume that misreads a passing artifact silently repeats finished work.

REVIEW_PASS
