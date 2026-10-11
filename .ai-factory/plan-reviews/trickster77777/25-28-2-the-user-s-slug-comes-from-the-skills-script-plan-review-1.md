## Plan Review Summary

**Plan:** 28.2 — the user's slug comes from the skills' script
**Files the plan targets:** `orchestrator/main.py`, `tests/test_main.py`
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap:** OK. The task is the open `28.2` line in `.ai-factory/roadmaps/trickster77777.md` (Phase 28). Its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/0065-the-users-slug-comes-from-the-skills-script.md`, and the plan follows every "What must be true after" clause in that spec: the constant, the three exit-code branches, the two new halts with their first lines, the removals, and the test changes.
- **Governing spec:** Checked against `docs/features/named-roadmaps.md` § What it is (the literal `"my"`) and `docs/concepts/fault-handling.md` § The known faults ("From the environment" row "A user-slug script that is missing or fails — A halt"). Both docs already describe the target behaviour, so "Docs: no" is correct. No other doc, `ARCHITECTURE.md`, `README.md` or `CLAUDE.md` describes the in-process derivation (grep for `slug` / `derive`). One divergence from the governing doc is listed under Critical Issues.
- **Architecture:** OK. `.ai-factory/ARCHITECTURE.md` is present. Running a subprocess from `main.py`'s resolution step fits how `_git_config_value` already shells out to `git`, and no new module or dependency edge is added.
- **Rules:** WARN. There is no `.ai-factory/RULES.md` and no `.ai-factory/skill-context/aif-review/SKILL.md`, so these gates were skipped.

### Codebase verification

- `main.py` matches the spec's "What is true now": `import re` is used only on the `re.sub` line inside `_derive_identity_slug._slugify` (grep for `\bre\.` finds nothing else). `_git_config_value` and `_resolve_roadmap_relpath` look as the plan describes. The identity halt message the plan quotes is the one in the code today, byte for byte.
- `cli()` takes `str(e).splitlines()[0]` for the `HALTED` detail. The two-line shape the plan uses for the new halts (fixed clause first, then path or stderr) therefore gives the right detail, the same way the `Named roadmap not found` and owner-mismatch halts next to it do.
- The installed script at `~/.claude/skills/roadmap-engine/scripts/user-slug.sh` (through the `~/.claude/skills` → `skills/active/skills` symlink) follows the contract the plan states: it prints the bare slug and exits `0`, exits `2` when no slug can be derived, and exits `1` with stderr when `git` is missing. It is tracked as `100755`.
- Tests: the import list, the four `test_derive_identity_slug_*` tests with their banner, `_fake_git_config`'s signature `_run(cmd, cwd=None, capture_output=None, text=None)`, and the seven `"my"` resolution tests all exist under the names the plan uses. The script call uses the same keyword arguments, so the extended stand-in will accept it. `Path.exists()` follows symlinks, so a broken symlink at the install path correctly gives the "not found" halt. No other test exercises `"my"` resolution: `test_config.py` only checks that the value loads.
- Patching `main_module._USER_SLUG_SCRIPT` through a module-global read at call time is correct and is called out explicitly in the plan. Pointing every `"my"` test at a `tmp_path` stand-in keeps the suite independent of the developer's `~/.claude` install, which the spec requires.

### Critical Issues

1. **A script that exists but cannot be executed crashes the run instead of halting, which contradicts the governing doc.**
   The plan's `Assumption:` paragraph leaves the `OSError` from `subprocess.run` uncaught, calling it out of scope. The governing docs already decide this case:
   - `named-roadmaps.md` says the run halts "when the script fails in any other way";
   - `fault-handling.md` says the same in its "missing or fails → A halt" row.

   **What happens with the plan as written:** if the file at `_USER_SLUG_SCRIPT` is present but not executable (lost exec bit, a directory at that path, a `noexec` mount), `subprocess.run` raises `PermissionError` or `OSError`. That reaches `cli()`'s generic `except Exception` branch, so the operator gets a traceback and an `ERRORED` outcome. The docs promise a `HALTED` outcome with the `User-slug script failed` clause.

   The task spec only lists exit codes and does not cover this case, so there is no conflict to escalate. The governing doc settles it, and the fix stays inside `main.py`. Wrap the call and send it to the existing failure halt:
   ```python
   try:
       result = subprocess.run([str(_USER_SLUG_SCRIPT)], cwd=project_dir, capture_output=True, text=True)
   except OSError as e:
       raise HaltError(f"User-slug script failed\n{e}") from e
   ```
   Then remove the `Assumption:` paragraph from the plan's Context section, or rewrite it to say this case is covered. A test is optional under the silent-failure rule, since the wrong outcome is loud. If one is added, a stand-in that raises `PermissionError` on the script call can check the first line in the same way as `test_resolve_roadmap_relpath_my_script_failure_raises_halt`.

### Positive Notes

- The plan keeps the `email` / `name` reads for the owner check and keeps the exit-`2` halt message unchanged, so `cli()`'s `HALTED` detail for "no identity" stays exactly as it is today.
- The plan covers the "What breaks on contact" clause in the spec: every existing `"my"` test gets an installed stand-in script and the slug the script would print, and their assertions are left alone.
- By default the stand-in returns exit `2` (no `slug`, no `script_returncode`), so any `"my"` test that forgets to pass a slug fails with the identity halt instead of silently passing.
- The two new tests check first lines exactly (`==`) and use the same pattern as the existing first-line test, which is the protection the spec asks for against a wrong `HALTED` detail.
- The order of the work is correct: the stand-in is extended before the new halt tests that depend on it, and the full suite run is the last step.

## Deferred observations

- Affects: skills repo, `src/skills/roadmap-engine/scripts/user-slug.sh`. The script's header comment says it "Derives the slug the way the pipeline does". Once this task lands, the pipeline no longer derives the slug itself. It runs this script, so the comment points at itself and suggests a second derivation that no longer exists. The comment should describe the derivation on its own terms, as the one source both sides use. This sits outside the orchestrator's file boundary.
