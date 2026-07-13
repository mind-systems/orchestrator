> Owner: trickster77777@gmail.com

# Project Roadmap

> Orchestrator — AI-driven multi-agent pipeline that autonomously plans, implements, and reviews code milestones.

## Self-hosting hardening

The orchestrator generates every project's code — including its own — so a silent defect here multiplies across the whole fleet: a wrong result is x10 outside, x100 at scale. This direction hardens the tool's own correctness — per-project configuration and artifact numbering below.

### Phase 3 — Per-project configuration

`load_config()` (`config.py:23`) reads one global `orchestrator.json` (or the `ORCHESTRATOR_CONFIG` path) and applies it to every target project uniformly — `max_iterations`, usage thresholds, `enable_phase_sessions`, Telegram routing, and `roadmap_path` are all fleet-wide. There is no way for project A to run with different settings than project B without editing the global file back and forth. The behavior ТЗ is written doc-first in `docs/configuration.md` § Оверлей под проект (already done); this task implements to it.

- [x] **3.1 — Per-project config overlay — different projects, different settings** — add `load_config(project_dir: Path | None = None)`: load and validate the global base as today (the four required keys still required in the base), then if `project_dir/.ai-factory/orchestrator.json` exists, shallow-merge its keys over the base before building `OrchestratorConfig` — project keys win, absent keys inherit, the four required keys are NOT required in the override, `telegram_alerts` replaces (not unions), and the override's `roadmap_path` gets the same relative/no-`..` guard then flows through the existing three-state resolver unchanged. Malformed override JSON → `SystemExit` naming the override path. `cli()` (`main.py:490`) passes the run's resolved project dir so the overlay applies before roadmap resolution. Absence of the override file is byte-stable — identical to today (hard acceptance). Unit tests in `test_config.py` pin byte-stable absence, precedence, partial override, list-replace, the guard, and malformed JSON. Spec: `.ai-factory/specs/trickster77777/21-per-project-config-overlay.md`. [9m 43s]

### Phase 4 — Artifact numbering correctness

`_next_number` (`main.py:84`) finds the next artifact index by lexicographically sorting the dir's `*.md` and taking the last digit-prefixed stem + 1 — a lexicographic-vs-numeric sort trap. Numbers are `:02d` (minimum width, not fixed), so once a per-roadmap artifact dir crosses 100 files, `"100-y.md"` sorts before `"99-x.md"` and the function returns 100 while `100-y.md` already exists — a duplicate-number collision. Surfaced as a deferred observation on the `_next_number` tests milestone, where the fix lay outside that test-only boundary.

- [ ] **4.1 — `_next_number`: pick by numeric max, not lexicographic last** — replace the `sorted(glob) → reversed → first digit-prefix + 1` logic (`main.py:89-92`) with a numeric max: over every `*.md`, parse the leading digit run of the stem (`stem.split('-',1)[0]` when `isdigit()`), return `max(...) + 1`; no digit-prefixed file → keep the `len(existing) + 1` fallback; empty dir → `1`. Kills the width-boundary collision (`99-x.md` + `100-y.md` → `101`, not the already-used `100`). The empty and all-non-digit contracts stay byte-identical — the only behavior change is at mixed digit widths (≥100). Update the `_next_number` characterization test that pinned the buggy mixed-width case (`['9-a.md','10-b.md']`) to assert the corrected max-based result, and add the explicit 99/100→101 boundary case. Touch `main.py` + `tests/test_main.py` only. Spec: `.ai-factory/specs/trickster77777/22-next-number-numeric-fix.md`.

---STOP---

- [ ] **Interactive REPL mode** — Bare `uv run orchestrator` (no subcommand) currently defaults to implement on current dir. Replace with an interactive session: load config from `~/.orchestrator.json`, display settings on entry, prompt `>` with readline history. Commands: `implement <path>`, `test <path>`, `set <key> <value>` (type-validated, in-session only), `show`, `save` (atomic write to config file via tmp+replace), `help`, `exit`. Ctrl+C during pipeline → stop run, return to prompt. New `orchestrator/repl.py`; `cli()` routes `args.command is None` to `run_repl(config, config_path)`; `load_config()` return type changes to `tuple[OrchestratorConfig, Path]`. Zero new dependencies — `readline` (stdlib). Update `CLAUDE.md` Commands section; mention REPL in `docs/workflow.md`. Spec: `.ai-factory/specs/trickster77777/01-repl.md`.
