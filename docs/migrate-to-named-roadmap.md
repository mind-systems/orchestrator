# Migrating a project to a user-scoped (named) roadmap

A short sequence to move a project from the shared `ROADMAP.md` to a per-developer named roadmap. Full mechanics live in [Configuration](configuration.md) and [How it works](how-it-works.md); this is just the steps.

## Steps

1. **Override config.** Create `<project>/.ai-factory/orchestrator.json` — git-ignored and per-developer, never committed:

   ```json
   { "roadmap_path": "my" }
   ```

   It overrides the global config for this project only: the orchestrator derives your roadmap from your git identity. Leave the global `orchestrator.json` alone — it keeps pointing at the shared roadmap, so projects that haven't migrated behave exactly as before. Each developer sets up their own override (and copies it into the next project they migrate).

2. **Slug** is derived automatically: the local-part of `git config user.email`, lowercased, each run of non-alphanumeric characters collapsed to a single hyphen (`john.doe@example.com` → `john-doe`). If the email is unset, it falls back to `user.name`.

3. **Roadmaps** → `.ai-factory/roadmaps/`:
   - `.ai-factory/ROADMAP.md` → `.ai-factory/roadmaps/<slug>.md`
   - `.ai-factory/ROADMAP_TESTS.md` → `.ai-factory/roadmaps/<slug>-tests.md`

   The first line of each file must be `> Owner: <your git email>`. In `"my"` mode it is verified against the current git identity; a mismatch or an unrecognized first line is an operational stop.

4. **Specs** → `.ai-factory/specs/<slug>/`: move the roadmap's task specs there and rewrite the `Spec:` tags in the roadmap lines to `specs/<slug>/…`.

5. **test-runs** (if any) → `.ai-factory/test-runs/<slug>/`.

6. **Verify.** Run the orchestrator against the project — it should resolve `roadmaps/<slug>.md` from your git identity. Artifact directories (`plans/`, `plan-reviews/`, `reviews/`, `test-runs/`) are created under `<slug>/` automatically; the main and test roadmaps share one numbering axis under the `<slug>` stem.
