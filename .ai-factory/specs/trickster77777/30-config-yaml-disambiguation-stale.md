# Drop the stale config.yaml disambiguation from configuration.md

**Date:** 2026-07-20
**Source:** conversation context (cross-repo follow-up to the skills repo's 19.1)

## Problem today

`orchestrator/docs/configuration.md` describes the orchestrator's per-project overlay and, to prevent confusion, disambiguates it against another tool's config:

> Оверлей оркестратора живёт в собственном `orchestrator.json` внутри `.ai-factory/` проекта — его не следует путать с `.ai-factory/config.yaml`, конфигом AI-Factory (другого инструмента).

The trailing clause disambiguates `orchestrator.json` against `.ai-factory/config.yaml` — the aif-family config. The sibling skills repo retired that artifact in its task 19.1 (`skills/.ai-factory/roadmaps/trickster77777.md`, Phase 19): `aif` no longer generates `.ai-factory/config.yaml`, and the three machinery files behind it are deleted. So the disambiguation now warns a reader off confusing `orchestrator.json` with an artifact that no future project will have — it points at nothing.

## The change

Doc-only edit, one sentence in `orchestrator/docs/configuration.md`:

- Keep the positive fact — the orchestrator's overlay lives in its own `orchestrator.json` inside the project's `.ai-factory/`. Drop the "его не следует путать с `.ai-factory/config.yaml`, конфигом AI-Factory (другого инструмента)" clause, which disambiguates against a retired artifact. The sentence becomes a plain statement of where the overlay lives.
- The doc is Russian (present-tense governing prose); the reworded sentence stays Russian and matches the surrounding register.

## Verify

- `grep -rn 'config\.yaml' orchestrator/docs/` → no hit that presents `.ai-factory/config.yaml` as a live artifact to disambiguate against.
- The overlay paragraph still states, in Russian, that the orchestrator's overlay is `orchestrator.json` inside the project's `.ai-factory/`.
- `git diff --stat` touches only `orchestrator/docs/configuration.md` — no code, no other doc.

## What NOT to do

- Do **not** touch the merge rules above the sentence, the agent-models table below it, or the overlay's own semantics — only the stale disambiguation clause changes.
- Do **not** reach into the sibling skills repo — this edit is confined to the orchestrator repo; the config.yaml retirement it follows from already landed there under 19.1.
- Do **not** switch the doc's language — it is Russian; keep it Russian.

## Tests

None. The doc is present-tense prose (a loud-failure surface — a wrong statement is caught by reading, not by a silent wrong result); verification is the `grep` and `git diff --stat` above.
