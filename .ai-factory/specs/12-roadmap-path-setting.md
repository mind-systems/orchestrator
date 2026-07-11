# Roadmap-path setting — named roadmaps threaded through the `roadmap_filename` seam

Governing spec: `~/projects/skills/docs/multiuser-roadmaps.md` — layout, slug rule, owner line, single-writer invariant, resolution order. On conflict, that file wins. Origin handoff: `.ai-factory/handoffs/03-multiuser-named-roadmaps-orchestrator-side.md` (note: the handoff's "no identity derivation" narrowing is superseded — the governing spec itself names the orchestrator among the resolvers of "my roadmap" that verify the owner line).

## Current state

Multiuser named roadmaps are ratified: per-developer queues live at `.ai-factory/roadmaps/<slug>.md` with a test sibling `<slug>-tests.md` beside each; the default `ROADMAP.md`/`ROADMAP_TESTS.md` pair stays a first-class citizen. The skills-repo half is decomposed (Phase 4 there; 4.1 — the engine's named-roadmap contract — already landed). The orchestrator takes the roadmap from **its own settings** — an environment-level value provisioned with the workstation.

Today the orchestrator hardcodes the pair. `_implement_loop` defaults `roadmap_filename="ROADMAP.md"` (`main.py:344`) and `cli()` never overrides it; `_test_loop` hardcodes `ROADMAP_TESTS.md` (`main.py:333`) and uses `TEST_MODE` without `_replace`. `Mode.roadmap_filename` (`main.py:41,57`) is re-joined under `.ai-factory/` in `process_milestone` (`main.py:126`). `config.py` has no roadmap key. Separately, `prompts/reviewer.md` fixes the roadmap by name twice: the plan-review root-recovery gate (line 25) matches the plan title against `ROADMAP.md`/`ROADMAP_TESTS.md` only — on a named roadmap the gate silently skips — and the milestone-alignment check (line 23) reads `ROADMAP.md` only.

The seam already carries most of the change: both joins (`main.py:126,346`) are `pathlib` `/`-joins that accept a multi-segment relative path as-is. The parameter's *semantics* widen (filename → relative path under `.ai-factory/`); the join code does not.

## Change

1. **Config key** — `config.py`: add optional `roadmap_path: str | None = None` to `OrchestratorConfig`; load via `data.get("roadmap_path") or None`; NOT in `required`. **Three explicit states — no null-implies-derivation magic:**
   - **absent** → default `ROADMAP.md`. Byte-stable; unmigrated projects and the transition period run exactly as today.
   - **literal `"my"`** → the family derivation, same rules as `roadmap-engine`'s named-roadmap contract: slug = `git config user.email` local-part, lowercase, every non-alphanumeric run → one hyphen (`kg.wmservice@gmail.com` → `kg-wmservice`); fallback = slugified `user.name`; target = `roadmaps/<slug>.md`. The `> Owner: <email>` first line is verified against the current git identity — **mismatch = `HaltError`** naming the owner (operational stop, yellow — not a milestone failure). **File missing → loud console fallback to `ROADMAP.md`** (one line stating the derived path and the fallback) — lazy migration: one workstation setting serves migrated and unmigrated projects alike.
   - **any other value** → explicit relative path under `.ai-factory/` (e.g. `"roadmaps/alice.md"` — running a specific/foreign queue is legitimate), used as-is, **no owner check** — explicit wins, per the governing spec's resolution order.
   Loud guard at load: an absolute path or any `..` segment → `SystemExit` with the offending value. Home is `orchestrator.json` — environment-level, per-workstation, gitignored; the target project's `config.yaml` is shared between developers, so a per-developer value there would violate single-writer (settled — do not move it there).
2. **Resolution helpers** — in `main.py`: pure `_derive_identity_slug(email: str | None, name: str | None) -> str | None` (the slug rule above; both empty → `None` → treat as derivation failure, `HaltError` telling the user to set git identity or an explicit path) and a thin `_resolve_roadmap_relpath(config, project_dir) -> str` that reads `git config user.email`/`user.name`, applies the three states, and performs the owner-line check (first line of the file, exact form `> Owner: <email>`).
3. **Widen the seam** — rename `roadmap_filename` → `roadmap_relpath` in the `Mode` field (`main.py:29,41,57`) and the `_implement_loop` parameter, documenting the new semantics: *path relative to `.ai-factory/`*. No join changes. `_implement_loop` signature becomes `roadmap_relpath: str | None = None`; resolve `roadmap_relpath or _resolve_roadmap_relpath(...)` — explicit argument → setting → default, mirroring the family-wide order. Generalize the missing-file message to name the actual path (`ERROR: No roadmap found at {path}`).
4. **Test sibling derivation** — pure helper `_tests_sibling(relpath: str) -> str`: exact `"ROADMAP.md"` → `"ROADMAP_TESTS.md"` (the default pair is a named special case, NOT `-tests` suffixing); anything else → same directory, stem + `"-tests.md"` (`roadmaps/kg-wmservice.md` → `roadmaps/kg-wmservice-tests.md`). `_test_loop` resolves the main relpath exactly as step 3 (including `"my"` and its fallback), derives the sibling, and uses `TEST_MODE._replace(roadmap_relpath=sibling)`. The sibling is **always derived from the roadmap in play, never from identity and never configured independently** — no second config key (mirrors the governing spec and skills task 4.1).
5. **Reviewer prompt** — widen the two hardcodes in `prompts/reviewer.md`: the root-recovery gate (line 25) matches the plan title against `.ai-factory/ROADMAP.md`, `.ai-factory/ROADMAP_TESTS.md`, **or any `.ai-factory/roadmaps/*.md`** (the `roadmaps/` directory is the enumeration point per the governing spec — listing it here is sanctioned); the alignment check (line 23) says "the roadmap in play — `.ai-factory/ROADMAP.md` or a named roadmap under `.ai-factory/roadmaps/`". Wording-level edits only; the gate's skip-if-no-match tail survives.
6. **Tests** — every new surface fails silently (a wrongly derived slug or path reads or creates the wrong queue — no crash), so per the testing philosophy each pure piece gets unit tests: `_derive_identity_slug` (the spec's canonical example, punctuation runs, empty email → name fallback, both empty → None), the owner-line check (match / mismatch → `HaltError` / malformed first line), the three-state resolution (absent → default; `"my"` + file present + owner ok → named; `"my"` + file missing → default; explicit → verbatim), `_tests_sibling` (the two mappings), and config loading (absent key → `None`, pass-through, absolute/`..` → `SystemExit`).
7. **Docs** — `docs/configuration.md` gains the `roadmap_path` key with all three states; `docs/target-project.md` gains one paragraph: a named roadmap under `.ai-factory/roadmaps/` may be the target, selected by this setting.

## Pinned forks

- **`"my"` + named roadmap exists + default `ROADMAP.md` still has pending tasks** → the named roadmap runs. Draining the shared default is an explicit act (unset the key or point at `ROADMAP.md`) — auto-picking shared leftovers from N workstations concurrently would recreate the very cross-user collision this direction removes.
- **`"my"` + derivation fails** (no email, no name in git config) → `HaltError` with the hint from the governing spec: set git identity or pass an explicit path. Never a silent default.

## Files & types

- edit `orchestrator/config.py` (`OrchestratorConfig.roadmap_path`, `load_config`)
- edit `orchestrator/main.py` (`Mode.roadmap_relpath` rename, `_derive_identity_slug`, `_resolve_roadmap_relpath`, `_implement_loop`, `_test_loop`, `_tests_sibling`)
- edit `orchestrator/prompts/reviewer.md` (two wording widenings)
- add tests in `tests/` (slug derivation, owner gate, three-state resolution, sibling derivation, config key)
- edit `docs/configuration.md`, `docs/target-project.md`

## Guards

- **Byte-stable default is the hard acceptance criterion**: with no `roadmap_path` key, every run is behavior-identical to today — same files, same messages, same artifacts; the existing pytest suite passes unmodified.
- **Derivation only under the explicit `"my"` keyword** — absence of the key never derives; an explicit path never owner-checks. The three states are disjoint by string value.
- **Artifact dirs stay flat in this task** — per-roadmap artifact subdirectories are task 13 (`.ai-factory/specs/13-artifact-subdirs.md`), separately revertible; sidecar and commit flows untouched here.
- `agents.py` untouched except that `HaltError` is already importable — the planner/implementer receive `roadmap_path` explicitly per call.
- `roadmap.py` (`mark_done`/`mark_skipped`/`parse_roadmap`) untouched — already path-agnostic.
- Lazy migration: no code creates `.ai-factory/roadmaps/` or writes owner lines — the orchestrator only reads; named roadmaps are born through the skills family.

## Verification

- `uv run pytest` green, including the new tests.
- `grep -n "roadmap_filename" orchestrator/` → zero hits (rename complete); `grep -n "ROADMAP_TESTS.md" orchestrator/main.py` → only the `_tests_sibling` special case and the `Mode` default.
- Live, `"my"`: git identity `kg.wmservice@gmail.com`, `roadmaps/kg-wmservice.md` present with matching owner line → implement run reads milestones from it; with a mismatched owner line → yellow halt naming the owner; with the file absent → one loud fallback line, run proceeds on `ROADMAP.md`.
- Live, explicit: `"roadmap_path": "roadmaps/alice.md"` → that queue runs, no owner check; test run targets `roadmaps/alice-tests.md` without any second setting.
- Live, default: key removed → run is indistinguishable from a pre-change run.
