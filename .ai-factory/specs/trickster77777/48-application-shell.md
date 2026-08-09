# An application shell: two panes, two modes, a hint bar

**Date:** 2026-08-09
**Source:** conversation context (Phase 22, `docs/future/operator-surface.md` § "The shape")

## Problem today

Nothing in the project imports an interface toolkit — `pyproject.toml` declares `dependencies = []`. `cli()` (`main.py`) parses `implement`/`test`/no-subcommand and, on no subcommand, defaults straight to `run_implement` on the current directory. There is no shell to hold a tree, a pane, or anything else Phase 22 builds on top of.

## The change

**1. The dependency, chosen and justified.** Criteria: built-in widgets for a directory tree, a scrollable text pane, and a modal dialog (so `22.1` and `22.4` are not building three widgets from nothing); a model for reading a long-running child's output without blocking the UI (`22.3` needs this); active maintenance; a small, well-known transitive footprint.

Against the alternatives:
- **`curses`** (stdlib, zero dependency) — no tree widget, no modal, no scrollback pane; every one of the shape's elements would be hand-built. Rejected: the dependency this task is explicitly told to accept exists precisely to avoid this.
- **`prompt_toolkit`** — built for line-editing and REPL-style prompts, and this surface is not a line-oriented prompt; its full-screen layout support is secondary to that use case.
- **`urwid`** — mature and stable, but its widget catalog has no directory tree out of the box, and its callback-driven event loop is a worse fit for streaming a child process's output (`22.3`) than a message-passing model.
- **Chosen: `textual`.** Ships `DirectoryTree`, a scrollable `RichLog`/`Log` pane, and modal `Screen`s natively; its async event loop and `run_worker` API are built for exactly the "read a child's output without blocking the UI" shape `22.3` needs; actively maintained; single new top-level dependency (`rich` arrives transitively, already a natural fit for rendering agent output).

`pyproject.toml`'s `dependencies = []` becomes `dependencies = ["textual"]`.

**2. The left pane has two modes.** One is a filesystem tree, rooted where the application was launched. The other lists the projects a run has been started against, enumerated straight from the records themselves, per `docs/future/operator-surface.md` § "A run's record": "the list of records is the set of records" — nothing else is kept to name them, so there is nothing that can drift out of agreement with what is actually there. A record is a directory under `~/.orchestrator/runs/`, one per project — under the orchestrator's own home, never inside any target project, because `_git_commit` (`main.py:177-189`) runs `git add -A` in the target project's tree after every task, so anything written inside that tree rides into that project's own commit history. Each record directory holds a `project` file whose content is the absolute path it belongs to, so that path is recoverable from the record itself rather than from a name that has to encode it — the directory's own name carries no meaning the list mode depends on. The list mode's entries are exactly the projects named by the records found under `~/.orchestrator/runs/`. At this task's point no run has ever been started from the surface, so the list mode may legitimately be empty — it shows nothing, not a placeholder or an example. This task only reads records to render the list; it writes none — that begins in `22.3`, when a run is first started.

The current selection is readable in either mode and means the same thing in both: the project a run would start against. Whichever mode is showing, one attribute (or bound reactive value) another task reads gives that project's path.

**3. The hint bar.** A bar along the bottom of the application, its entries left-aligned, each a key and the action it performs — the shape a file manager's function-key bar has (`F1 Help`, `F2 Rename`, and so on). It is the one place the application's available actions are listed; a task that adds a key adds its entry here, never a second list elsewhere. At this task's point in the chain the bar holds exactly two entries — the layout toggle and the mode toggle — because no run can be started yet.

**4. The layout toggle.** The bar's first entry toggles the arrangement of the left pane and the output pane between side-by-side and stacked (one above the other), bound to `l` — a single lowercase letter, matching the shape `i`/`t` (`22.3`) will register beside it. The bar shows it as `l Layout`. The same key remains the layout toggle for every later task that adds its own entry beside it.

**5. The mode toggle.** The bar's second entry switches the left pane between its tree and list modes, bound to `m` — a single lowercase letter, the same shape as `l`. The bar shows it as `m Mode`. The same key remains the mode toggle for every later task; nothing else binds it.

**6. Entry-point change**, `main.py`'s `cli()`: when `args.command is None` (no subcommand), launch the shell instead of defaulting to `run_implement`. `implement <path>` and `test <path>` keep calling `run_implement`/`run_test` exactly as today, unchanged.

## Guards

- This task starts no run and renders no output into the pane — the pane exists and is empty. `22.3` is what makes `i`/`t` do anything.
- The tree mode's root is the directory the process was launched from (`Path.cwd()`), not a configured or prompted path.
- Records live under `~/.orchestrator/runs/`, each one created (with the parent directory, on first use) by whichever task first writes one (`22.3`) — never under any `project_dir` or its `.ai-factory/`. This task only reads what's already there, and tolerates none existing yet (an empty list, not an error). There is no separate index file — the list mode enumerates the record directories directly.
- `implement <path>` and `test <path>` subcommands are untouched — only the no-subcommand default changes.
- The dependency choice is local to this task's spec — do not thread `textual` imports into `agents.py`, `usage.py`, or any module that doesn't need them yet.
- The hint bar is the one place an available action is listed — no task adds a second legend, a tooltip, or a help screen duplicating it.
- `l` is reserved for the layout toggle and `m` for the mode toggle, both from this task onward — no later task binds either to anything else, and the two stay distinct keys.

## Tests

Loud surface — a missing dependency or a broken import fails at `uv run orchestrator` startup, not silently. No unit test asserts terminal rendering; a smoke test may assert the shell module imports cleanly and the `App` subclass instantiates without raising, matching this repo's silent-failure test philosophy (test what fails quietly, not what fails loudly).

## Verify

- `uv sync` picks up `textual`.
- `uv run orchestrator` (no args) opens the shell instead of running `implement` on the current directory.
- `uv run orchestrator implement <path>` and `uv run orchestrator test <path>` behave exactly as before.
- The hint bar shows `l Layout` and `m Mode` along the bottom; pressing `l` switches the tree/output-pane arrangement between side-by-side and stacked, and pressing `m` switches the left pane between its tree and list modes, both readable as the same selected project across the switch.
- With no records under `~/.orchestrator/runs/` — the directory itself absent — the list mode shows an empty list, not an error.
- `uv run pytest` green.

## What NOT to do

- Do not wire `i`/`t`, do not start a run, do not touch `_run_claude` or any agent class — that is `22.3`.
- Do not add a settings screen — that is `22.4`.
- Do not create a record directory under `~/.orchestrator/runs/` — this task only reads what is already there.
- Touch `pyproject.toml`, the new shell module, and `main.py`'s `cli()` entry-point routing only.
