# A missing personal roadmap is a halt

**Date:** 2026-10-11
**Source:** the user's ruling in chat on 2026-10-10, «если стоит май=тру в настройке, а мой роадмап почему то не достижим, мы не можем начать пытаться выполнять дефолтный роадмап. Это странное проглатывание ошибки»

Governing spec: [named-roadmaps.md](../../../docs/features/named-roadmaps.md) — § What it is, the literal `"my"`; [fault-handling.md](../../../docs/concepts/fault-handling.md) — the row "A named roadmap that does not exist".

## What is true now

`_resolve_roadmap_relpath(config, project_dir)` in `orchestrator/main.py` has a branch for `roadmap_path == "my"`. It reads `user.email` and `user.name`, derives the slug, and builds `relpath = f"roadmaps/{slug}.md"`. When `.ai-factory/<relpath>` does not exist, the branch prints `>>> Named roadmap {relpath} not found — falling back to ROADMAP.md` and returns `"ROADMAP.md"`, so a run configured for a developer's own queue executes the shared one without stopping.

When the file exists, the branch compares its first line to `> Owner: <email or name>` and, on a mismatch, raises `HaltError` whose first line is the fixed clause `Named roadmap owner line does not match the current git identity`, with the relpath, the quoted first line and the expected owner on the line below. A halt's message opens with a fixed clause and carries anything variable below it; `cli()` reports the first line as the halt's detail. An identity from which no slug can be derived already raises `HaltError`.

`tests/test_main.py` holds `test_resolve_roadmap_relpath_my_missing_file_falls_back`, which asserts the call returns `"ROADMAP.md"` for an absent file.

## What must be true after

The `"my"` branch raises `HaltError` when `.ai-factory/<relpath>` does not exist. Its first line is exactly `Named roadmap not found`; the next line is the expected path, `.ai-factory/` joined with the relpath (`.ai-factory/roadmaps/john-doe.md` for the slug `john-doe`). The print line is gone, and the branch returns no roadmap in place of the missing one.

`test_resolve_roadmap_relpath_my_missing_file_falls_back` becomes a halt test: `HaltError` is raised, the first line of its message is `Named roadmap not found`, and the rest of the message contains `roadmaps/john-doe.md`. The first line is what the `HALTED` alert carries; a wrong clause there reaches the operator as a wrong detail and nothing else fails.

Behaviour otherwise is unchanged: the owner check, the identity halt and the explicit-path state stay as they are.

## What breaks on contact

- `_implement_loop` and `_test_loop` resolve their roadmap through this function whenever no roadmap path is handed to them, so a run configured with `"my"` and no personal roadmap file stops with a halt before any task instead of running `ROADMAP.md`. Nothing else in `orchestrator/` calls it.
- A project that set `"my"` before creating its personal roadmap halts until the roadmap is moved into place; `named-roadmaps.md` and `fault-handling.md` already state this.
