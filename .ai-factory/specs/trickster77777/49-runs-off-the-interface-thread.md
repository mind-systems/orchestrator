# `i` and `t` start runs that the interface outlives

**Date:** 2026-08-09
**Source:** conversation context (Phase 22, `docs/future/operator-surface.md` § "`i` and `t` start runs that the interface outlives"); contract laid by `22.2`; revised — a run started from the surface is a child process, not a worker inside the application

## Problem today

Reading a child's output blocks for as long as the child runs, and a run lasts hours, so that read cannot sit on the interface's own thread — a shell that blocked on it would freeze the tree, the projects list, and every key binding for the run's entire length, the opposite of what a full-screen application is for. `22.1`'s shell has both left-pane modes and an empty output pane but no way to start a run yet.

## What this task inherits from `22.2`

`22.2` already stated the boundary as a contract — what crosses between the surface and a child process, in which direction, and the scenarios that prove it — against a fake child, no real subprocess. This task is the real wiring that satisfies that contract: it does not restate what may cross the boundary, it launches a real child and builds the record-keeping and rendering around it.

## The change

**1. Launching the child.** `i`/`t`, bound to the left pane's current selection, launch a child process running `implement <path>` / `test <path>` against that project — the same invocation a terminal would run, spawned instead from the shell. The pipeline inside that child is **not modified by this task at all**: it still writes to its own stdout and still exits on completion, exactly as it does today from a terminal. Nothing in `agents.py`, `runtime.py`, or `main.py` changes.

**2. One record per project.** Records are keyed by project path, matching `docs/future/operator-surface.md`'s own invariant that a project has at most one live run: `i`/`t` against a project already running shows that run in flight rather than launching a second child.

**3. Reading without blocking.** The child's stdout is read off the interface's own thread — this is the one place a genuine background read is unavoidable, since consuming a pipe is itself a blocking call. Each line read is appended to that project's record as it arrives, per `22.2`'s contract; the record accumulates lines whether or not it is the one currently shown.

**4. Rendering the selected record.** The output pane always shows the currently selected record's lines; switching the left pane's selection switches which record's lines are visible, with no re-reading and no re-running — the record already holds what a finished or in-flight run has produced.

**5. Stopping.** The interface's stop action ends the selected record's child, per `22.2`'s contract — idempotent, and it does not discard lines already received.

**6. Closing.** When the application closes, every child still running is ended with it, per `22.2`'s fourth scenario — no orphaned process survives the surface that started it.

## Guards

- The pipeline itself is untouched — this task's whole premise is that a child process needs no cooperation from the code running inside it. No import of `agents.py`'s or `main.py`'s pipeline functions; the child is launched as a process, not called as a function.
- A project's record and its child are one-to-one; a second `i`/`t` against a running project is a no-op beyond showing what's already in flight.
- Reading the child's stdout happens off the interface's own thread; nothing about rendering a record blocks on a child that is still producing output.
- Do not widen what crosses the boundary beyond `22.2`'s contract — this task builds the real child and record-keeping, it does not renegotiate what they exchange.

## Tests

Process-spawning and stream-reading is a loud surface (a broken invocation fails immediately, per this repo's own silent-failure test philosophy) and is not unit-tested here. `22.2`'s four scenarios, red against its fake child, are this task's acceptance test — filling in the real child (or a thin wrapper the same scenarios can drive) turns them green; no new scenario is authored here.

## Verify

- `uv run pytest` green, including `22.2`'s four scenarios now passing against the real (or a thin real-backed) child.
- `uv run orchestrator` (no args), pressing `i` on a fixture project with a pending task, starts a run whose output streams into that project's record and into the output pane while the left pane stays responsive throughout.
- Starting a second run against a different project while the first is still going leaves both running, each with its own record; selecting either project shows only its own output.
- The stop action ends the selected project's child and leaves its record in place; closing the application ends every still-running child.
- `uv run orchestrator implement <path>` (no shell) behaves exactly as today.

## What NOT to do

- Do not call `run_implement`/`run_test` in-process, or import from `agents.py` — the child is a separate process, launched the same way a terminal would launch it.
- Do not touch `runtime._handle_sigint`, its `signal.signal` registration, or `agents.kill_active_child` — those belong to the non-shell entry point and are unrelated to ending a child the shell itself launched.
- Do not rebind `l` — the layout toggle stays `22.1`'s; this task only adds `i`/`t`.
- Do not restate or renegotiate `22.2`'s contract — build to it.
- Touch the shell module and its tests only.
