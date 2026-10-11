# Named-roadmap resolution lives in layout.py

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11, «давай декомпоуз 29» and «ставим и сохраняем»

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules and § Folder Structure.

What diverges now: [.ai-factory/specs/trickster77777/0067-modules-do-not-yet-follow-the-layer-map.md](0067-modules-do-not-yet-follow-the-layer-map.md).

## What is true now

This is the tree as the tasks above it leave it.

`orchestrator/main.py` holds, beside the flow, the composition root and the CLI:

- `_USER_SLUG_SCRIPT`, the installed `user-slug.sh` under `Path.home() / ".claude"`;
- `_git_config_value(project_dir, key) -> str | None`;
- `_resolve_roadmap_relpath(config, project_dir) -> str`, which raises `HaltError` from `errors`;
- `_tests_sibling(relpath) -> str` and `_artifact_subdir(relpath) -> str | None`.

`_implement_loop` calls `_resolve_roadmap_relpath` when no roadmap path is handed to it, and `_artifact_subdir`; `_test_loop` calls `_resolve_roadmap_relpath`, `_tests_sibling` and `_artifact_subdir`.

`tests/test_main.py` imports `_resolve_roadmap_relpath`, `_tests_sibling` and `_artifact_subdir` from `main`. The `test_resolve_roadmap_relpath_my_*` tests patch `main_module.subprocess.run` through `_fake_git_config`, and the helper `_install_slug_script` and the missing-script test patch `main_module._USER_SLUG_SCRIPT`.

## What must be true after

A new `orchestrator/layout.py` defines `_USER_SLUG_SCRIPT`, `_git_config_value`, `_resolve_roadmap_relpath`, `_tests_sibling` and `_artifact_subdir`, bodies unchanged. From the package it imports `errors` and `config` only.

`main` imports them from `layout`. The resolution tests import them from `layout`, and their patches on `main_module.subprocess` and `main_module._USER_SLUG_SCRIPT` become patches on `layout.subprocess` and `layout._USER_SLUG_SCRIPT`.

The change is behaviour-neutral: the resolution states, halts and messages are as before.

## What breaks on contact

- `main_module._USER_SLUG_SCRIPT`, patched in `_install_slug_script` and in `test_resolve_roadmap_relpath_my_missing_script_raises_halt`, no longer exists once the name moves; a patch left there raises `AttributeError`.
- `main_module.subprocess.run`, patched in the `test_resolve_roadmap_relpath_my_*` tests, replaces `run` on the stdlib `subprocess` module itself. Left behind, it keeps intercepting `layout`'s calls for as long as `main` imports `subprocess`, so those tests pass while naming the wrong module; they move to `layout`.
- The `_artifact_subdir` and `_tests_sibling` tests only import; their import line changes.
