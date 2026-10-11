## Plan Review Summary

**Plan:** 29.6: named-roadmap resolution lives in `layout.py`
**Files Reviewed:** plan, spec `0073-named-roadmap-resolution-lives-in-layout.md`, `ARCHITECTURE.md` (§ Dependency Rules, § Folder Structure, § Anti-Patterns), `orchestrator/main.py`, `orchestrator/errors.py`, `orchestrator/claude_cli.py`, `orchestrator/config.py`, `orchestrator/__init__.py`, `tests/test_main.py`, `tests/conftest.py`
**Risk Level:** 🟢 Low

### Context Gates
- **Roadmap:** OK. The plan matches contract line 29.6 in `.ai-factory/roadmaps/trickster77777.md`, which is the next open task after 29.5. It also covers every "What must be true after" and "What breaks on contact" item in spec 0073.
- **Architecture:** OK. `layout.py` sits in the "Roles and adapters" layer, and its only package imports are `errors` and `config` (both vocabulary), so its imports point downward. `main` (the composition root) imports `layout`, which the rules allow. `layout` launches `git` and `user-slug.sh`, not the `claude` CLI, so it does not break the "claude CLI only in `claude_cli.py`" anti-pattern rule.
- **Rules:** WARN (non-blocking). `.ai-factory/RULES.md` does not exist.

### Verification against the codebase
- `main.py` currently holds the five moved names as one contiguous block (`_USER_SLUG_SCRIPT` → `_artifact_subdir`). The block sits between `_next_number` and `_artifact_dir`, as the plan says.
- After the move, `main.py` still uses every import it has today:
  - `subprocess` in `_git_commit` and in the `git add` inside `process_task`
  - `Path` throughout
  - `HaltError` in the plan-review guard in `process_task` and in `cli`'s `except HaltError`
  - `OrchestratorConfig` in several signatures

  The plan is right not to drop any import.
- Only `_test_loop` and `_implement_loop` call the moved names, and only through `_resolve_roadmap_relpath`, `_tests_sibling` and `_artifact_subdir`. Those are exactly the three names the plan imports into `main`. Nothing in `main` uses `_USER_SLUG_SCRIPT` or `_git_config_value`, so leaving them out of the import is correct.
- In `tests/test_main.py`, every patch that has to move is on the plan's list:
  - `main_module._USER_SLUG_SCRIPT`, patched in `_install_slug_script` and in the missing-script test
  - `main_module.subprocess`, patched in all the `_my_*` tests, including the multi-line form in the missing-script and script-failure tests and the `_run` stand-in in the not-executable test

  No test patches the three resolution functions on `main_module`, and `conftest.py` has no autouse patches.
- The plan says `_resolve_roadmap_relpath` must keep finding `_USER_SLUG_SCRIPT` and `subprocess.run` by module-level lookup in `layout`. That is what keeps `layout_module` patches effective. A by-value import (`from subprocess import run`) would make them silently ineffective, so this is the right constraint.
- The `__init__.py` file is empty, and `pyproject.toml` does not list modules, so the new module needs no packaging change.
- The verification greps are sound. The `main.py` grep matches on `def` for the three re-imported functions, so the new import line will not produce a false match.

### Critical Issues
None.

### Positive Notes
- The plan names the silent trap behind this move. A patch on `main_module.subprocess.run` actually patches the stdlib module, so a leftover patch would keep the tests passing while naming the wrong owner. The plan moves those patches explicitly instead of relying on the tests to fail.
- The plan pins the baseline test count (227) and requires the same count afterwards, which is the right check for a behaviour-neutral move.
- The module header follows the pattern of its sibling modules (`errors.py`, `claude_cli.py`).

PLAN_REVIEW_PASS
