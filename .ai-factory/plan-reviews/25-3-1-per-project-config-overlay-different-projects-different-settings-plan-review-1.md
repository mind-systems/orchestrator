## Plan Review Summary

**Plan:** 3.1 — Per-project config overlay
**Files Reviewed:** plan + `config.py`, `main.py` (`cli()`), `tests/test_config.py`, governing spec `.ai-factory/specs/21-per-project-config-overlay.md`, ТЗ `docs/configuration.md § Оверлей под проект`
**Risk Level:** 🟢 Low

### Context Gates
- **Architecture** (`.ai-factory/ARCHITECTURE.md`): WARN — none. The change widens the existing config seam (`Project-root config file`, `992a38e`) without crossing any module boundary; no dependency-direction impact.
- **Rules** (`.ai-factory/RULES.md`): not present — skipped.
- **Roadmap** (`.ai-factory/ROADMAP.md:87`): PASS — the plan is the direct decomposition of milestone `3.1`, whose `Spec:` tag names `.ai-factory/specs/21-per-project-config-overlay.md`, itself deferring to `docs/configuration.md § Оверлей под проект`. Verified the plan against that whole tree; every clause conforms.
- **Skill-context** (`aif-review/SKILL.md`): not present — no project overrides to apply.

### Correctness / Faithfulness
All ground-truth references in the plan were checked against the live files and are accurate:

- `load_config()` signature widening to `load_config(project_dir: Path | None = None)` — matches spec §22 exactly.
- Cited line anchors are all correct at HEAD: `config.py:37-38` is the base `JSONDecodeError → SystemExit` handler the override mirrors; `config.py:46` is the `roadmap_path` guard; `config.py:49-57` is the `.get()`-of-known-keys construction; `main.py:490` is `config = load_config()`; `main.py:488` already resolves `project_dir`.
- The one behavioral reorder (moving the guard below `data.update(override)`) is sound: with `project_dir is None` no override is read and `data` is untouched, so the guard runs on identical bytes — the byte-stable-absence invariant (spec §24, §48) holds. Guard message text and semantics are preserved.
- Partial-override handling is correct: the four-required-keys check runs only against the base; construction reads override values via `data["..."]` after `update`, and `.get()` for optional keys — so unknown keys are ignored and required keys are never re-demanded (spec §30-31, §65).
- `telegram_alerts` list-replace-not-union falls out of `dict.update` naturally; the plan correctly refuses to special-case it and pins it with a test (spec §34).
- Threading in Task 2 places the overlay before `run_implement`/`run_test`, hence before `_resolve_roadmap_relpath` reads `config.roadmap_path` — satisfying spec §38's ordering requirement.
- No other caller of `load_config()` exists in product code (only `main.py:490` and tests), so the new optional parameter is backward-compatible with every existing call site.
- Test plan (Task 3) covers all six spec-mandated cases and correctly reuses `_write_config` / `ORCHESTRATOR_CONFIG` without duplicating base-validation coverage (spec §46-54).

### Notes (non-blocking, spec-conformant)
- When a **override**-supplied `roadmap_path` trips the guard, the raised message names the base file path (the `path` variable), not the override file — because the guard message is deliberately kept identical. This is intentional and ratified by the governing spec: §33 requires the override path in the message only for the malformed-JSON case, and the guard test (§52, and the plan's own case) asserts only that the offending *value* appears. Conformance, not a defect — flagged only so the implementer keeps the message unchanged rather than "helpfully" rewording it.

### Positive Notes
- The plan is exceptionally precise: every edit is anchored to a verified line, and the byte-stable-absence invariant is reasoned through rather than asserted.
- Correctly scopes out the forward-compat REPL return-type change (spec §42) and the `.ai-factory/config.yaml` confusion (spec §67) — no scope creep.
- Merge-order reasoning (guard and construction both on the merged `data`) means `roadmap_path` from an override flows through the unchanged three-state resolver for free — no duplicated logic.

PLAN_REVIEW_PASS
