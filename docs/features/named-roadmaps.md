# Named roadmaps

## What it is

An optional per-developer roadmap, in place of the shared `ROADMAP.md`, so each developer's own task queue runs independently.

The `roadmap_path` field selects which roadmap the orchestrator reads. It has three mutually exclusive states:

- **Absent, or an empty string** — `ROADMAP.md` is used; behaviour is identical to a run without this setting at all (byte-stable by default).
- **The literal `"my"`** — the orchestrator derives a personal roadmap from this workstation's git identity: the slug is built from the local part of `git config user.email` (falling back to `user.name` if the email is unset), lowercased, with every run of non-alphanumeric characters collapsed to a single hyphen (`john.doe@example.com` → `john-doe`). The target file is `.ai-factory/roadmaps/<slug>.md`. If the file exists, its first line must be `> Owner: <email>`, matching the current git identity — a mismatch or an unrecognized first line stops the run with an operational halt naming the owner. If the file does not yet exist, the orchestrator logs this loudly once and continues on `ROADMAP.md` — a lazy migration, so the same workstation config works both before and after the named roadmap appears. If neither an email nor a name is set in git, the run halts with a prompt to configure a git identity or pass an explicit path.
- **Any other value** — an explicit relative path under `.ai-factory/` (for example, `"roadmaps/alice.md"`), used as-is, with no owner check — an explicit value always wins.

An absolute path, or a path containing a `..` segment, is a startup error naming the invalid value.

The test roadmap is always derived from the main one: `ROADMAP_TESTS.md` for the default roadmap, the same directory with a `-tests` suffix for a named one (`roadmaps/alice.md` → `roadmaps/alice-tests.md`). There is no separate setting for the test roadmap.

Artifact directories stay flat, byte-for-byte, for the default `ROADMAP.md`/`ROADMAP_TESTS.md` pair (`plans/`, `plan-reviews/`, `reviews/`, `test-runs/`). For any other (named) roadmap, artifacts move into a subdirectory keyed by the roadmap file's stem — for example, `roadmaps/john-doe.md` → `plans/john-doe/`, `reviews/john-doe/`. The named pair's test sibling shares that same subdirectory: `roadmaps/john-doe-tests.md` keys off the same stem, `john-doe`, as `roadmaps/john-doe.md` — both the implement- and test-mode artifacts of a named pair share one numbering axis, `plans/john-doe/`, exactly as the default pair shares its flat directories. This keeps each developer's `{NN}` numbering on its own axis, so merging branches never collides.

## Migrating an existing project

1. **Override config.** Create `<project>/.ai-factory/orchestrator.json` — git-ignored and per-developer, never committed:

   ```json
   { "roadmap_path": "my" }
   ```

   It overrides the global config for this project only: the orchestrator derives your roadmap from your git identity. Leave the global `orchestrator.json` alone — it keeps pointing at the shared roadmap, so projects that have not migrated behave exactly as before. Each developer sets up their own override (and copies it into the next project they migrate).

2. **Roadmaps** → `.ai-factory/roadmaps/`:
   - `.ai-factory/ROADMAP.md` → `.ai-factory/roadmaps/<slug>.md`
   - `.ai-factory/ROADMAP_TESTS.md` → `.ai-factory/roadmaps/<slug>-tests.md`

   The slug is derived automatically from your git identity, as described above. The first line of each file must be `> Owner: <your git email>`.

3. **Specs** → `.ai-factory/specs/<slug>/`: move the roadmap's task specs there and rewrite the `Spec:` tags in the roadmap lines to `specs/<slug>/…`.

4. **test-runs** (if any) → `.ai-factory/test-runs/<slug>/`.

5. **Verify.** Run the orchestrator against the project — it should resolve `roadmaps/<slug>.md` from your git identity. Artifact directories (`plans/`, `plan-reviews/`, `reviews/`, `test-runs/`) are created under `<slug>/` automatically; the main and test roadmaps share one numbering axis under the `<slug>` stem.
