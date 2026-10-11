# Plan: 28.1 — a missing personal roadmap is a halt

## Context
With `roadmap_path` set to `"my"`, `_resolve_roadmap_relpath` in `orchestrator/main.py` currently prints a fallback line and returns `"ROADMAP.md"` when `.ai-factory/roadmaps/<user-slug>.md` is absent, so a run meant for a developer's own queue silently executes the shared one. Per the task spec (`.ai-factory/specs/trickster77777/0064-a-missing-personal-roadmap-is-a-halt.md`) and the governing docs (`docs/features/named-roadmaps.md` § the literal `"my"`, `docs/concepts/fault-handling.md` row "A named roadmap that does not exist" — both already state the halt), that branch must raise `HaltError` instead. The docs need no change.

## Settings
- Testing: yes (the task explicitly converts the existing fallback test into a halt test)
- Logging: minimal
- Docs: no

## Tasks

### Halt on a missing personal roadmap

- [x] **Raise `HaltError` for an absent personal roadmap**
  Files: `orchestrator/main.py`
  In `_resolve_roadmap_relpath`, inside the `config.roadmap_path == "my"` branch, replace the `if not roadmap_file.exists():` body (the `print(f">>> Named roadmap {relpath} not found — falling back to ROADMAP.md")` line and `return "ROADMAP.md"`) with a raise shaped like the owner-mismatch halt directly below it — fixed clause on the first line, variable part on the next:
  ```python
  raise HaltError(
      f"Named roadmap not found\n"
      f".ai-factory/{relpath}"
  )
  ```
  The first line must be exactly `Named roadmap not found` (that is what `cli()` takes via `str(e).splitlines()[0]` as the `HALTED` alert detail). The second line is the expected path, `.ai-factory/` joined with `relpath` (e.g. `.ai-factory/roadmaps/john-doe.md`) — a project-relative path, not `roadmap_file`'s absolute one. Leave the identity halt, the owner check, the `None` state and the explicit-path state untouched. No change is needed in `_implement_loop` / `_test_loop`: both call this function outside any handler, so the `HaltError` propagates to `cli()`'s existing `except HaltError` and the run stops before any task. The docstring stays accurate as is.

- [x] **Turn the fallback test into a halt test** (depends on Raise `HaltError` for an absent personal roadmap)
  Files: `tests/test_main.py`
  Replace `test_resolve_roadmap_relpath_my_missing_file_falls_back` with a halt test (rename it, e.g. `test_resolve_roadmap_relpath_my_missing_file_raises_halt`, and update its docstring to state the halt, not a fallback). Keep its setup (`_fake_git_config(email="john.doe@example.com")`, no roadmap file created, `_config_with_roadmap_path("my")`). Follow the pattern of `test_resolve_roadmap_relpath_my_owner_mismatch_halt_has_fixed_first_line`: `with pytest.raises(HaltError) as exc:` around the call, then assert `str(exc.value).splitlines()[0] == "Named roadmap not found"` and that `"roadmaps/john-doe.md"` is in `str(exc.value).split("\n", 1)[1]`. Run `uv run pytest` and confirm the whole suite passes.
