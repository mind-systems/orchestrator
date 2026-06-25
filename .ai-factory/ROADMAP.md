# Project Roadmap

> Orchestrator — AI-driven multi-agent pipeline that autonomously plans, implements, and reviews code milestones.

## Hardening

- [x] **Caffeinate no-crash on non-macOS** — `_with_caffeinate` in `main.py` always spawns `caffeinate` via `Popen`, raising `FileNotFoundError` immediately on Linux. Wrap the `Popen` call with `try/except FileNotFoundError`: on failure, run the wrapped function directly without caffeinate and return the elapsed string. No behavior change on macOS. [3m 4s]

- [x] **Fix stderr pipe deadlock in `_run_claude`** — `stderr=subprocess.PIPE` combined with `proc.stderr.read()` called only after `proc.wait()` can deadlock if `claude` writes > ~64 KB to stderr before exiting: stderr pipe fills, subprocess blocks, our stdout loop stalls. Fix: replace `stderr=subprocess.PIPE` with `stderr=subprocess.STDOUT` to merge stderr into the stdout stream (already captured line by line). Remove the post-wait `proc.stderr.read()` call and the `stderr` variable from all downstream uses (`RuntimeError` messages). Touch `agents.py` only. [3m 14s]

---STOP---

- [ ] **Interactive REPL mode** — Bare `uv run orchestrator` (no subcommand) currently defaults to implement on current dir. Replace with an interactive session: load config from `~/.orchestrator.json`, display settings on entry, prompt `>` with readline history. Commands: `implement <path>`, `test <path>`, `set <key> <value>` (type-validated, in-session only), `show`, `save` (atomic write to config file via tmp+replace), `help`, `exit`. Ctrl+C during pipeline → stop run, return to prompt. New `orchestrator/repl.py`; `cli()` routes `args.command is None` to `run_repl(config, config_path)`; `load_config()` return type changes to `tuple[OrchestratorConfig, Path]`. Zero new dependencies — `readline` (stdlib). Update `CLAUDE.md` Commands section; mention REPL in `docs/workflow.md`. Spec: `.ai-factory/notes/01-repl.md`.
