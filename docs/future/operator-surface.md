# Operator surface

The surface is a full-screen application rather than a stream of lines, because the operator's questions are continuous ones — where a run would start, what is happening in it right now, what state it is in — and a scrolling log answers none of them at a glance.

## The shape

The left pane shows either a filesystem tree or the list of projects a run has been started against — two ways to name the same thing, a project, which is why one selection serves both: its current selection is the project a run starts against, whichever mode it is showing. A second pane carries the selected project's output as it arrives; one key starts an implement run and one a test run; settings open as a window in the same application; the available actions are visible on screen rather than memorised; the two panes sit side by side or one above the other, at the operator's choice.

## More than one run

The surface holds several runs at once. Starting one against a project leaves every other run untouched and running.

A project has at most one live run. The record is keyed by the project itself, so starting on a project that is already running shows the run in flight instead of beginning a second one — two runs over one project would write the same artifacts and commit into the same tree. This is a property of how the records are keyed, not a rule anyone has to remember.

A record outlives its run. Nothing is removed when a run ends, so one list is at once what is running now, where runs have happened before, and the place to start the next one.

Selecting a record shows that project's output and points the run keys at it, so starting a run again never requires navigating to the project a second time.

## A run's record

A record is a project and the output of its runs. It lives with the orchestrator, never inside the project it runs against: the run commits that project's tree as it works, so anything written there rides into that project's own history. See [target-project.md](../reference/target-project.md) for that commit behaviour. The location itself belongs in [configuration.md](../reference/configuration.md).

The list of records is the set of records. There is no second index alongside them to be kept in agreement.

Liveness is never part of a record at rest. A record on disk says where runs happened and what they printed; whether one is running now is known only while the application is. A stored answer to that question would go on claiming a run is alive after the application that owned it is gone.

No run outlives the application that started it. Closing it ends every run it started.

## The pipeline writes to its own stream, nothing more

The pipeline writes its account to its own output stream and nothing more; whoever holds that stream decides how it is shown. A terminal and a pane are two holders of one stream, not two implementations — the pipeline is unaware of which one has it.

## A run ends; the surface does not

A run's ending is its own, never the surface's — a finished or crashed run leaves the surface standing and its record in place. See [fault-handling.md](../concepts/fault-handling.md) for where classification lives.

## A report the surface can retry

A run reports its outcome by notification, and a notification can fail to leave the machine — routinely for the same reason the run stopped. A process about to exit attempts the send once and goes on; there is nothing more it can honestly do with what it cannot deliver.

An application that stays open can do more. While it is running it holds what its runs reported, so a send that failed is the surface's to attempt again rather than the run's to lose on the first try. What holds the report is not the run that wrote it — that run has exited — but the application that outlived it.

Whether an undelivered report survives a restart of the application itself is not decided here. That is a question about where such a thing would live and how long it is worth keeping, and it belongs to the task that builds the sending.

## The interface stays live

A run lasts hours, and the surface answers throughout: output arrives as it is produced, and stopping a run is an action taken in the interface rather than a signal aimed at the process. The interface never waits on the run, and the run never blocks the interface.

## Waiting is visible

A run retrying a transient fault says so in its own output, naming what it is retrying and which attempt it is on, so a retry in progress is never mistakable for a hang.

## Settings live where runs start

Configuration is read and changed in the same application that starts the run, and a change applies to the next run started from it. The keys themselves and their defaults stay in [configuration.md](../reference/configuration.md).

## The surface holds no policy

It renders; it does not classify a fault, decide what an outcome means, or absorb anything on the run's behalf. Every entry point reaches the same classification, none carries its own, and a caller that absorbs faults on the run's behalf leaves the run unable to survive the same fault when invoked any other way.

## What it is not

It does not replace invocation from a shell. A run started by a script, a wrapper, or a scheduler stays a first-class way to use the orchestrator, and every behaviour above holds identically for it; the surface is one caller among several, never the only one.

## Invariants

1. **The pipeline is unaware of what renders it.** It writes to its own output stream and asks no question about who is reading it — a terminal, a pane, or a log all see the same account unchanged.
2. **A run's ending never ends the surface.** A finished or crashed run leaves the surface standing, its record in place, free to start another.
3. **The interface answers while a run is in flight.** A run's length places no ceiling on how responsive the surface is, and stopping one is an action rather than a signal.
4. **A wait is visible as a wait.** A waiting run states what it waits for, so waiting and hanging are never presented the same way.
5. **The surface renders and holds no policy of its own.** Removing the surface changes nothing about how a fault is classified or an outcome decided.
6. **A run's record never lives inside the project it runs against.** Anything written there rides into that project's own history.
7. **A project has at most one live run.** A second start on a busy project shows the one in flight rather than beginning another.
8. **Liveness is never persisted.** No run outlives the application that started it.
