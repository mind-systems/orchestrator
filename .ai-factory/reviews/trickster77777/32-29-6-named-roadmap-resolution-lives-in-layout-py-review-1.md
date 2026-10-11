## Code Review Summary

**Files Reviewed:** 3 (`orchestrator/layout.py` (new), `orchestrator/main.py`, `tests/test_main.py`), plus the plan, spec `0073-named-roadmap-resolution-lives-in-layout.md`, and `.ai-factory/ARCHITECTURE.md`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture:** OK. `layout.py` is in the "Roles and adapters" layer. Its only package imports are `from .config import OrchestratorConfig` and `from .errors import HaltError`, which are both vocabulary modules, so its imports point downward. `main` is the composition root and imports `layout`, which the rules allow. Nothing in the package imports `main`. `layout` launches `git` and `user-slug.sh`, never the `claude` CLI, so it does not hit the "claude CLI only in `claude_cli.py`" anti-pattern.
- **Rules:** WARN (non-blocking). `.ai-factory/RULES.md` does not exist.
- **Roadmap:** OK. The change matches contract line 29.6 in `.ai-factory/roadmaps/trickster77777.md` and every "What must be true after" and "What breaks on contact" item in spec 0073.

### Verification
- **Bodies unchanged:** the block removed from `HEAD:orchestrator/main.py` and the body of the new `layout.py` are byte-identical under `diff`. This covers `_USER_SLUG_SCRIPT`, `_git_config_value`, `_resolve_roadmap_relpath`, `_tests_sibling` and `_artifact_subdir`. Every halt message and every resolution state stays as it was.
- **Imports in `main.py`:** `main.py` now imports `_artifact_subdir`, `_resolve_roadmap_relpath` and `_tests_sibling` from `.layout`, sorted with the other imports. It keeps all its existing imports, and each one is still used:
  - `subprocess` in `_git_commit` and `process_task`
  - `HaltError` in the plan-review guard and in `cli`
  - `Path` and `OrchestratorConfig`

  The call sites in `_test_loop` and `_implement_loop` have not changed.
- **Tests:** the resolution tests now import from `orchestrator.layout`. Every `main_module._USER_SLUG_SCRIPT` and `main_module.subprocess` patch is now on `layout_module`, including the multi-line forms and the `_run` stand-in in the not-executable test. `layout._resolve_roadmap_relpath` looks up `subprocess.run` and `_USER_SLUG_SCRIPT` at module level, so the moved patches take effect.
- **Plan's verification greps:**
  - `grep -nE 'main_module(\.subprocess|, "_USER_SLUG_SCRIPT")' tests/` has no matches.
  - The moved-name grep over `orchestrator/main.py` has no matches.
- **Test suite:** `uv run pytest` gives 227 passed, the same count as the baseline.

### Critical Issues
None.

### Positive Notes
- The move is mechanical. Bodies, order and docstrings are kept exactly, which is the right shape for a behaviour-neutral layering change.
- Moving the `subprocess` patches to `layout` makes them name their real owner. Leaving them on `main_module.subprocess` would have passed silently, because both names point to the same stdlib module.
- The new module's header (docstring, `from __future__ import annotations`, stdlib imports, then package imports) has the same shape as `errors.py`, `protocol.py` and `claude_cli.py`.

REVIEW_PASS
