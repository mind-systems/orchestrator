# The user's slug comes from the skills' script

**Date:** 2026-10-11
**Source:** the user's wish relayed by skills 07 on 2026-10-10, «желательно, что б оркестратор и скилы пользовались одним скриптом», after skills phase 83 landed the script; and the user's go in chat on 2026-10-11

Governing spec: [named-roadmaps.md](../../../docs/features/named-roadmaps.md) — § What it is, the literal `"my"`; [fault-handling.md](../../../docs/concepts/fault-handling.md) — the row "A user-slug script that is missing or fails".

## What is true now

This is the tree as the task "a missing personal roadmap is a halt" leaves it: an absent personal roadmap file raises `HaltError`.

`_derive_identity_slug(email: str | None, name: str | None) -> str | None` in `orchestrator/main.py`, with its inner `_slugify`, derives the slug: the lowercased, hyphen-collapsed local part of the email, else the same for the name, else `None`. It is the only user of `import re` in `main.py`.

The `"my"` branch of `_resolve_roadmap_relpath` reads `user.email` and `user.name` through `_git_config_value(project_dir, key)`, which returns the stripped value or `None` on a non-zero exit or an empty value. It passes both to `_derive_identity_slug`; when that yields `None` it raises `HaltError("roadmap_path is 'my' but no git identity is set — set git user.email or user.name, or use an explicit roadmap_path.")`. It then builds `roadmaps/<user-slug>.md`, halts if the file is absent, and compares the file's first line to the owner line built from `email or name`.

The skills package ships `user-slug.sh`, installed at `~/.claude/skills/roadmap-engine/scripts/user-slug.sh`. It reads the identity of the repository it runs in, prints the bare slug on one line and exits `0`; it exits `2` when no slug is derivable from the git identity, and any other exit is a failure.

Tests in `tests/test_main.py`: `_derive_identity_slug` is imported, and `test_derive_identity_slug_canonical_example`, `test_derive_identity_slug_punctuation_runs_collapse`, `test_derive_identity_slug_empty_email_falls_back_to_name` and `test_derive_identity_slug_both_empty_returns_none` exercise it. The resolution tests patch `main_module.subprocess.run` with `_fake_git_config(email=None, name=None)`, which answers by `cmd[-1]` being `user.email` or `user.name` and returns returncode `1` for any other command.

## What must be true after

`main.py` defines a module-level `_USER_SLUG_SCRIPT = Path.home() / ".claude" / "skills" / "roadmap-engine" / "scripts" / "user-slug.sh"`.

Under `"my"`:

- when the file at `_USER_SLUG_SCRIPT` does not exist, `HaltError` is raised with first line `User-slug script not found` and the script's path on the line below;
- otherwise `subprocess.run([str(_USER_SLUG_SCRIPT)], cwd=project_dir, capture_output=True, text=True)` runs:
  - exit `0` — the slug is the stripped stdout;
  - exit `2` — today's identity halt, its message unchanged;
  - any other exit — `HaltError` with first line `User-slug script failed` and the stripped stderr on the line below.

The roadmap path, the missing-file halt and the owner check follow unchanged. The owner check still reads email and name through `_git_config_value`.

`_derive_identity_slug`, `_slugify` and `import re` are removed from `main.py`.

Tests: the `_derive_identity_slug` import and the derivation tests named above go. The `subprocess.run` stand-in also answers the script call — exit `0` with a slug on stdout, or exit `2`. The resolution tests point `_USER_SLUG_SCRIPT` at an existing stand-in file under `tmp_path`. The derivation-failure resolution test becomes the exit-`2` test. A test for a missing script and a test for an exit other than `0` or `2` pin the first lines of those halts; a wrong clause there reaches the operator as a wrong `HALTED` detail and nothing else fails.

## What breaks on contact

- Under `"my"`, a run now needs the skills package active; without the installed script it halts before any task. This repository's own `.ai-factory/orchestrator.json` sets `"my"`. `named-roadmaps.md` already states the requirement.
- The resolution tests that today answer only `git config` calls fail on the script call until the stand-in answers it.
