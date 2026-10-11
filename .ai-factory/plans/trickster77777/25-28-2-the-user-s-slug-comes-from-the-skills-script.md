# Plan: 28.2 — the user's slug comes from the skills' script

## Context
Under `roadmap_path: "my"`, `_resolve_roadmap_relpath` in `orchestrator/main.py` derives the user-slug itself through `_derive_identity_slug` (with inner `_slugify`), while the skills package ships `user-slug.sh` for exactly that, so the two derivations can drift. Per the task spec (`.ai-factory/specs/trickster77777/0065-the-users-slug-comes-from-the-skills-script.md`), the orchestrator runs the installed script instead, and two new halts cover a missing or failing script. The governing docs already state this behaviour — `docs/features/named-roadmaps.md` § the literal `"my"` (the slug is whatever the script prints, run from `~/.claude/skills/roadmap-engine/scripts/user-slug.sh`; halts when not installed, on no identity, and on any other failure) and `docs/concepts/fault-handling.md` row "A user-slug script that is missing or fails" (a halt) — so no doc change is needed.

The script contract (from `~/.claude/skills/roadmap-engine/scripts/user-slug.sh`): prints the bare slug on one line and exits `0`; exits `2` when no slug is derivable from the git identity; any other exit is a failure, with the reason on stderr.

A file that exists at the install path but cannot be executed (lost exec bit, a directory, a `noexec` mount) makes `subprocess.run` raise `OSError`. The task spec lists only exit codes, but the governing docs settle this case — the run halts "when the script fails in any other way" (`named-roadmaps.md`) and on a script that "fails" (`fault-handling.md`) — so it goes to the same `User-slug script failed` halt.

## Settings
- Testing: yes (the task explicitly requires removing the derivation tests, extending the stand-in and adding one test per new halt)
- Logging: minimal
- Docs: no

## Tasks

### Run the script in place of the in-process derivation

- [x] **Add `_USER_SLUG_SCRIPT` and resolve the slug through it**
  Files: `orchestrator/main.py`
  1. Add a module-level constant (near the other module-level definitions, above `_git_config_value`):
     ```python
     _USER_SLUG_SCRIPT = Path.home() / ".claude" / "skills" / "roadmap-engine" / "scripts" / "user-slug.sh"
     ```
     `_resolve_roadmap_relpath` must read it by its global name at call time (not capture it as a default argument), so tests can monkeypatch `main_module._USER_SLUG_SCRIPT`.
  2. In `_resolve_roadmap_relpath`'s `config.roadmap_path == "my"` branch, replace `slug = _derive_identity_slug(email, name)` and the `if slug is None:` block with:
     - if `not _USER_SLUG_SCRIPT.exists()`: `raise HaltError(f"User-slug script not found\n{_USER_SLUG_SCRIPT}")`;
     - otherwise run the script, turning an `OSError` (present but not executable) into the failure halt:
       ```python
       try:
           result = subprocess.run([str(_USER_SLUG_SCRIPT)], cwd=project_dir, capture_output=True, text=True)
       except OSError as e:
           raise HaltError(f"User-slug script failed\n{e}") from e
       ```
     - `result.returncode == 0` → `slug = result.stdout.strip()`;
     - `result.returncode == 2` → raise today's identity `HaltError` with its message byte-for-byte unchanged (`"roadmap_path is 'my' but no git identity is set — set git user.email or user.name, or use an explicit roadmap_path."`);
     - any other code → `raise HaltError(f"User-slug script failed\n{result.stderr.strip()}")`.
     Both new halts follow the shape of the owner-mismatch and not-found halts beside them: the fixed clause alone on the first line (what `cli()` takes via `str(e).splitlines()[0]` as the `HALTED` detail), the path / stderr on the line below.
  3. Keep the `email = _git_config_value(project_dir, "user.email")` and `name = _git_config_value(project_dir, "user.name")` reads — the owner check (`identity = email or name`) still uses them. Leave the relpath construction, the `Named roadmap not found` halt, the owner check, the `None` state and the explicit-path state unchanged.
  4. Delete `_derive_identity_slug` (with its inner `_slugify`) and `import re` — `_derive_identity_slug` is the only user of `re` in `main.py`; confirm with a grep for `re.` before removing the import.

### Tests

- [x] **Drop the derivation tests and teach the stand-in the script call** (depends on Add `_USER_SLUG_SCRIPT` and resolve the slug through it)
  Files: `tests/test_main.py`
  1. Remove `_derive_identity_slug` from the `from orchestrator.main import (...)` list, and delete the `_derive_identity_slug` section: its banner comment and `test_derive_identity_slug_canonical_example`, `test_derive_identity_slug_punctuation_runs_collapse`, `test_derive_identity_slug_empty_email_falls_back_to_name`, `test_derive_identity_slug_both_empty_returns_none`.
  2. Extend `_fake_git_config` (update its docstring) so it also answers the script call:
     - `_Result` gains a `stderr` attribute (default `""`);
     - new keyword parameters: `slug=None`, `script_returncode=None`, `script_stderr=""`;
     - a call whose `cmd[0]` is not `"git"` is the script call: if `script_returncode` is set, return `_Result(script_returncode, "", script_stderr)`; elif `slug` is set, return `_Result(0, f"{slug}\n")`; else return `_Result(2, "", "user-slug.sh: neither user.email nor user.name yields a slug …")` (exit `2`, no identity);
     - `git config` calls keep today's behaviour keyed on `cmd[-1]`.
  3. Add a helper, e.g. `_install_slug_script(tmp_path, monkeypatch)`, that writes a placeholder file at `tmp_path / "slug-bin" / "user-slug.sh"` (create the parent) and monkeypatches `main_module._USER_SLUG_SCRIPT` to it — the content is irrelevant because `subprocess.run` is patched. Call it in every `"my"` resolution test so none depends on the real `~/.claude` install.
  4. Update the existing `"my"` tests to pass the slug the script would print: `test_resolve_roadmap_relpath_my_present_matching_owner`, `..._my_missing_file_raises_halt`, `..._my_owner_mismatch_raises_halt`, `..._my_owner_mismatch_halt_has_fixed_first_line`, `..._my_malformed_first_line_raises_halt` → `slug="john-doe"`; `..._my_name_derived_owner_matches` → `slug="alice"`. Their assertions stay as they are.
  5. Turn `test_resolve_roadmap_relpath_my_derivation_failure_raises_halt` into the exit-`2` test: rename (e.g. `test_resolve_roadmap_relpath_my_script_exit_2_raises_identity_halt`), docstring stating the script reports no derivable slug, stand-in with no `slug` (exit `2`), assert `HaltError` and that its first line starts with `roadmap_path is 'my' but no git identity is set`.

- [x] **One test per new halt** (depends on Drop the derivation tests and teach the stand-in the script call)
  Files: `tests/test_main.py`
  Add next to the other `_resolve_roadmap_relpath` halt tests, following `test_resolve_roadmap_relpath_my_owner_mismatch_halt_has_fixed_first_line`'s pattern (`pytest.raises(HaltError) as exc`, then `splitlines()[0]` and `split("\n", 1)[1]`):
  - `test_resolve_roadmap_relpath_my_missing_script_raises_halt`: monkeypatch `main_module._USER_SLUG_SCRIPT` to a non-existent path under `tmp_path`, patch `subprocess.run` with `_fake_git_config(email="john.doe@example.com", slug="john-doe")`; assert first line `== "User-slug script not found"` and the patched path's string is in the remainder.
  - `test_resolve_roadmap_relpath_my_script_failure_raises_halt`: `_install_slug_script(...)`, stand-in with `script_returncode=1, script_stderr="user-slug.sh: git is not installed\n"`; assert first line `== "User-slug script failed"` and `"user-slug.sh: git is not installed"` in the remainder.
  - `test_resolve_roadmap_relpath_my_script_not_executable_raises_halt`: `_install_slug_script(...)`, and a `subprocess.run` stand-in that raises `PermissionError("Permission denied")` when `cmd[0]` is not `"git"` (delegating `git config` calls to `_fake_git_config(email="john.doe@example.com")`); assert first line `== "User-slug script failed"`.
  Run `uv run pytest` and confirm the whole suite passes.
