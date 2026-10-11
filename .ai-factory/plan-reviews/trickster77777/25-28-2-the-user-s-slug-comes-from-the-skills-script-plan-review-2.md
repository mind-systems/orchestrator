## Plan Review Summary

**Plan:** 28.2 — the user's slug comes from the skills' script
**Files the plan targets:** `orchestrator/main.py`, `tests/test_main.py`
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap:** OK. The task is the open `28.2` line in `.ai-factory/roadmaps/trickster77777.md` (Phase 28), right below the `[x]` 28.1 line at the seam. Its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/0065-the-users-slug-comes-from-the-skills-script.md`. The plan covers every clause in the spec's "What must be true after":
  - the `_USER_SLUG_SCRIPT` constant;
  - the not-found halt;
  - the `subprocess.run([str(_USER_SLUG_SCRIPT)], cwd=project_dir, capture_output=True, text=True)` call;
  - exit `0`, exit `2` and any other exit;
  - removing `_derive_identity_slug`, `_slugify` and `import re`;
  - the owner check unchanged;
  - all the test changes.
- **Governing spec:** OK. `docs/features/named-roadmaps.md` § What it is (the literal `"my"`) and `docs/concepts/fault-handling.md` (row "A user-slug script that is missing or fails — A halt") already describe the target behaviour, so "Docs: no" is right. A grep of `docs/`, `orchestrator/` and `tests/` finds no other description of the in-process derivation. `test_config.py` only checks that `"my"` loads, so this change does not touch it.
- **Architecture:** OK. Running the script from `main.py`'s resolution step is the same pattern `_git_config_value` already uses to shell out to `git`. No new module or dependency edge is added.
- **Rules:** WARN. There is no `.ai-factory/RULES.md` and no `.ai-factory/skill-context/aif-review/SKILL.md`, so these gates were skipped.

### Resolution of the previous review

Plan review 1 had one finding: a script that exists but cannot be executed would raise `OSError` out of `subprocess.run` and reach `cli()` as `ERRORED`, while the docs promise a halt. The plan now fixes this:
- It wraps the call in `try/except OSError` and sends the error to the `User-slug script failed` halt, chaining it with `from e`.
- The Context section now gives the doc wording that requires the halt, in place of the earlier `Assumption:` paragraph.
- A third halt test (`..._my_script_not_executable_raises_halt`, with a `PermissionError` stand-in) pins the first line.

`PermissionError` is a subclass of `OSError`, so the test exercises the new branch. The finding is closed.

### Codebase verification

- **`main.py` matches the spec's "What is true now":**
  - `import re` appears only on the `re.sub` line inside `_derive_identity_slug._slugify`.
  - The `"my"` branch reads `email`/`name`, derives the slug, and raises the identity halt with the exact message the plan quotes.
  - The branch then builds `roadmaps/{slug}.md`, halts on `Named roadmap not found`, and checks the owner line against `email or name`.
  - The plan keeps the two `_git_config_value` reads for the owner check, which is correct.
- **First line of the halt:** `cli()` takes `str(e).splitlines()[0]` for the `HALTED` detail. With the two-line shape (fixed clause, then path or stderr), the first line is the clause even when stderr is empty, because `"User-slug script failed\n".splitlines()[0]` is the clause.
- **Installed script:** `~/.claude/skills/roadmap-engine/scripts/user-slug.sh` is present and executable (`-rwxr-xr-x`). It behaves as the plan describes:
  - prints the slug with `printf '%s\n'` and exits `0`;
  - exits `2` with a stderr reason when neither identity yields a slug;
  - exits `1` with a stderr reason when `git` is missing.

  The plan's default stand-in output for exit `2` and its exit-`1` stderr in the failure test copy these real messages.
- **Test stand-in:** `_fake_git_config`'s `_run(cmd, cwd=None, capture_output=None, text=None)` accepts the script call's keyword arguments. The plan sends a call to the script branch when `cmd[0] != "git"`, before the `cmd[-1]` key lookup. Without that check the script path would fall through to `returncode 1`, so the order matters, and the plan has it right. When no slug is given, the stand-in defaults to exit `2`, so a `"my"` test that forgets the slug fails with the identity halt instead of passing silently.
- **Existing tests:** all seven `"my"` resolution tests and the four `test_derive_identity_slug_*` tests (with their banner comment) exist under the names the plan uses. The slugs the plan assigns (`john-doe` for the email-based tests, `alice` for the name-fallback test) match the roadmap files and assertions those tests already have.
- **Test isolation:** `_resolve_roadmap_relpath` reads `_USER_SLUG_SCRIPT` as a module global when it runs, so `monkeypatch.setattr(main_module, "_USER_SLUG_SCRIPT", …)` takes effect. Pointing every `"my"` test at a placeholder under `tmp_path` keeps the suite independent of the developer's `~/.claude` install, which the spec requires.

### Critical Issues

None.

### Positive Notes

- The plan states the script contract once, taken from the installed script itself, and builds the stand-in's default and failure outputs from those real messages.
- The new halts copy the shape of the `Named roadmap not found` and owner-mismatch halts beside them, so the operator's `HALTED` detail looks the same for every resolution halt.
- The new tests compare first lines exactly (`==`). That is the protection the spec asks for: a wrong clause here only shows up as a wrong `HALTED` detail and would fail nothing else.
- The task order is correct: the code change comes first, then the stand-in, then the per-halt tests, and the full `uv run pytest` run is the last step.

## Deferred observations

- Affects: skills repo, `src/skills/roadmap-engine/scripts/user-slug.sh`. The script's header comment says it "Derives the slug the way the pipeline does". Once this task lands, the pipeline runs this script instead of deriving the slug itself, so the comment describes a second derivation that no longer exists and in effect points back at the script. It should describe the derivation on its own terms, as the one source both sides use. This is outside the orchestrator's file boundary. [routed → skills/.ai-factory/specs/trickster77777/0245-the-slug-scripts-header-names-no-caller.md]

PLAN_REVIEW_PASS
