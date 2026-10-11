## Code Review Summary

**Files Reviewed:** 2 (`orchestrator/main.py`, `tests/test_main.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **Roadmap:** OK. This implements the open `28.2` line in `.ai-factory/roadmaps/trickster77777.md` (Phase 28). Every clause under "What must be true after" in its spec, `.ai-factory/specs/trickster77777/0065-the-users-slug-comes-from-the-skills-script.md`, is met: the `_USER_SLUG_SCRIPT` constant, the missing-script halt, the `subprocess.run([str(_USER_SLUG_SCRIPT)], cwd=project_dir, capture_output=True, text=True)` call, the exit 0/2/other branches, the removal of `_derive_identity_slug`/`_slugify`/`import re`, and the test changes.
- **Governing spec:** OK. Checked against `docs/features/named-roadmaps.md` § the literal `"my"` and the `docs/concepts/fault-handling.md` row "A user-slug script that is missing or fails". The `OSError` → `User-slug script failed` branch puts the docs' "fails in any other way" case into code, as plan-review 1 asked. No doc change is needed.
- **Architecture:** OK. The subprocess call sits next to `_git_config_value`'s existing `git` shell-out, in the same module. No new dependency edge.
- **Rules:** WARN. There is no `.ai-factory/RULES.md` and no `.ai-factory/skill-context/aif-review/SKILL.md`.

### Verification

- `import re` is gone from `main.py`, and nothing else in `main.py` used it. `roadmap.py`, `usage.py` and the tests import `re` themselves.
- `_resolve_roadmap_relpath` reads `_USER_SLUG_SCRIPT` as a module global when it is called, so the tests' `monkeypatch.setattr(main_module, "_USER_SLUG_SCRIPT", …)` takes effect.
- Every halt keeps its fixed clause alone on the first line, which matches what `cli()` takes as the `HALTED` detail through `str(e).splitlines()[0]`. The exit-2 message is unchanged byte for byte.
- The owner check still reads `email`/`name` through `_git_config_value`.
- `uv run pytest`: 226 passed.
- A live resolution against this repository with `roadmap_path="my"` ran the installed script and returned `roadmaps/trickster77777.md`.
- The tests: every `"my"` test points `_USER_SLUG_SCRIPT` at a stand-in under `tmp_path`, except the missing-script test, which points it at an absent path on purpose. So the suite does not depend on the developer's `~/.claude`. The stand-in's default is exit 2, so a test that forgets to pass a slug fails loudly. The two new halts are pinned with `==` on their first lines.

### Critical Issues

None.

### Positive Notes

- The `try/except OSError ... from e` keeps the original cause in the chain while showing the operator a `HALTED` outcome instead of `ERRORED`.
- The tests change only what the plan named. The setup and assertions of the existing tests are left alone apart from the stand-in arguments.
- The not-executable case gets its own small test, and its stand-in reuses `_fake_git_config` for the `git config` calls.

## Deferred observations

- Affects: skills repo, `src/skills/roadmap-engine/scripts/user-slug.sh`. The script's header comment says it "Derives the slug the way the pipeline does". Now that the pipeline runs this script and no longer derives the slug itself, the comment refers back to itself. It should describe the derivation on its own terms. This is outside the orchestrator's file boundary.

REVIEW_PASS
