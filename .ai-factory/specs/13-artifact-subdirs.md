# Per-roadmap artifact subdirectories — users never share a number axis

Governing spec: `~/projects/skills/docs/multiuser-roadmaps.md` (amended alongside this task: the artifact-flatness carve-out is revised — see Rationale). Depends on task 12 (`.ai-factory/specs/12-roadmap-path-setting.md`): the subdirectory key is derived from the resolved roadmap relpath that task introduces.

## Rationale — why the original "artifacts stay flat" pin is revised

The flat layout rested on the premise that orchestrator artifacts are branch-local. Ground truth says otherwise: `_git_commit` runs `git add -A` (`main.py:96`), so `plans/`, `plan-reviews/`, `reviews/`, `test-runs/` ride every milestone commit, reach the integration branch via PR, and return into **every** developer's working copy on rebase/merge. Flat dirs therefore become the union of all users' queues, with three concrete failure modes:

1. **Duplicate numbers** — two developers run concurrently on their own branches; each `_next_number` (`main.py:82`) counts only its local files; after both merge, the flat dir holds two different plans with the same `NN`. Every later `_next_number` and any tooling that treats `NN` as an axis reads a corrupted sequence.
2. **Foreign-plan adoption** — the resume detector (`resume.py:76`) globs `*-{slug}.md` by slug alone; a merged foreign plan with a recurring title (same slug) gets adopted together with its sidecar (worst case `step: done` → `mark_done` + commit with zero work). Task 14 gates adoption by in-flight state; this task removes the cross-user half of the surface entirely.
3. **Filename merge conflicts** — same `NN` and same slug from two developers is a real git conflict on merge.

## Change

1. **Subdirectory key** — pure helper in `main.py`, `_artifact_subdir(relpath: str) -> str | None`: the default pair (`"ROADMAP.md"`, `"ROADMAP_TESTS.md"`) → `None` (flat, byte-stable); anything else → the roadmap file's stem (`roadmaps/kg-wmservice.md` → `"kg-wmservice"`, `roadmaps/kg-wmservice-tests.md` → `"kg-wmservice-tests"`, a track file like `ROADMAP.watch.md` → `"ROADMAP.watch"`). The key comes from the resolved relpath — never from git identity; the orchestrator still derives nothing beyond task 12's `"my"` resolution.
2. **Threading** — `Mode` gains a field `artifact_subdir: str | None = None`; the loop setup that already does `MODE._replace(roadmap_relpath=...)` also sets `artifact_subdir=_artifact_subdir(relpath)`. In `process_milestone`, when the field is set, `plans_dir`, `plan_reviews_dir`, and the mode's `output_dir` each gain the subdirectory segment (`ai_factory / "plans" / subdir`, …); `mkdir(parents=True)` already handles creation. `_next_number` and `_detect_step` receive the subdir'd paths through the existing parameters — **no change in `resume.py` and no change in the numbering mechanism**: numbering is per-directory as built, exactly the argument the governing spec used for `specs/<slug>/`.
3. **Consequences owned by the layout** — each roadmap's artifacts start at `01` in a fresh subdirectory; implement- and test-mode plans of a named pair land in sibling subdirs (`plans/<slug>/` vs `plans/<slug>-tests/`) instead of sharing one number axis — separate dirs, no filename contact, no ordering contract between them.
4. **Tests** — `_artifact_subdir` fails silently (wrong key → artifacts land in a foreign dir — no crash): unit tests pin the four mappings above. One integration-shaped test over the existing detector fixtures: with a subdir'd `plans_dir`, resume dispatch is unchanged (the fixtures just point one level deeper).
5. **Docs** — `docs/how-it-works.md` and `CLAUDE.md` (file-protocol paragraph): artifact dirs are flat for the default pair, per-roadmap subdirectories keyed by the roadmap stem for everything else.

## Files & types

- edit `orchestrator/main.py` (`_artifact_subdir`, `Mode.artifact_subdir`, dir construction in `process_milestone`, both loop setups)
- add tests in `tests/`
- edit `docs/how-it-works.md`, `CLAUDE.md`

## Guards

- **Byte-stable default**: the default pair maps to `None` → flat dirs, identical paths, existing suite green unmodified.
- **`resume.py` untouched** — the detector's contract (dirs in, dispatch out) already absorbs the layout; the in-flight adoption gate is task 14, not here.
- **Protocol mirrors live in the skills repo** — `orchestrator-artifacts` (layout description; it also still documents the retired `patches/` bridge — same sweep), `roadmap-prune`'s artifact sweep. They are skills-roadmap tasks, not this one; this task only changes the orchestrator and this repo's docs.
- No migration of existing flat artifacts — old files stay where they are; the subdir applies from the first run after the change.

## Verification

- `uv run pytest` green.
- Live, named: `roadmap_path: roadmaps/kg-wmservice.md` → first milestone produces `plans/kg-wmservice/01-….md` + sidecar, reviews under `reviews/kg-wmservice/`, plan-reviews under `plan-reviews/kg-wmservice/`; interrupt + resume mid-milestone dispatches identically to flat.
- Live, default: no key → paths byte-identical to a pre-change run (`plans/NN-….md`).
