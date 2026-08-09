# Future spec: consolidating run-state into `RunContext`

> Status: **not queued**. Deliberately deferred — entering here is a decision to
> make, not a missing precondition: the behaviour net this refactor needs already
> exists (see "Order" below). This is an improvement in readability and
> testability, and **not** a defect fix — the current code works.

## What's wrong today

`orchestrator/state.py` holds six module-level mutable globals for the process:

```python
stop_requested: bool = False                     # whether a soft stop was requested (Ctrl+C)
active_proc: subprocess.Popen | None = None       # the active claude CLI child process
run_started: float | None = None                  # monotonic timestamp of the run's start
tasks_done: int = 0                               # how many tasks this run has closed
config: OrchestratorConfig | None = None          # the current config
project_dir: Path | None = None                   # the run's target project
```

The problem isn't the globals themselves, but that **three different modules read
and mutate them**, with no single owner of the state:

- `stop_requested` — set in `runtime._handle_sigint`, read in the run loops (`main.py`).
- `active_proc` — set in `agents._run_claude`, read/cleared in
  `agents.kill_active_child` (called by both `_run_claude` and `runtime._handle_sigint`).
- `run_started` — set at the start of `main.run_implement`/`run_test`, read in `runtime._run_elapsed`.
- `tasks_done` — incremented in `main.py` after `mark_done`, read in `runtime._run_summary`.
- `config` / `project_dir` — stashed at the start of `run_implement`/`run_test`, read in
  `runtime._handle_sigint` for the force-quit notification.

Two consequences follow:

1. **Implicit coupling.** Understanding who owns a piece of state means grepping the
   whole project — there's no single place that shows the run's lifecycle.
2. **Test boilerplate.** Every test touching these functions must save and restore
   the globals in `try/finally` (as the `_run_summary` tests already do), or state
   leaks between tests.

## What this is NOT

This is **not** broken code. Module-level globals are a legitimate pattern for a
single-process CLI, and the existing tests prove it's tested as it stands. The
refactor's value is exactly two things: removing the implicit coupling and freeing
the tests from boilerplate.

The operator surface starts each run as its own child process, one run per
process — so module-level globals stay a legitimate pattern, and nothing above this
doc will ever require it to be built. This remains an improvement in readability
and testability, never a precondition for another piece of work; the reason to do
it is the coupling and the test boilerplate it removes, nothing else.

## Target shape

Collect the six fields into a single context object, created at the start of a run
and **passed explicitly** through the pipeline instead of mutating module globals:

```python
@dataclass
class RunContext:
    config: OrchestratorConfig
    project_dir: Path
    run_started: float
    stop_requested: bool = False
    active_proc: subprocess.Popen | None = None
    tasks_done: int = 0
```

- `run_implement`/`run_test` create the `RunContext` and thread it through the
  loops, `process_task` (`main.py:198`), and the lifecycle helpers.
- The signal handler (`_handle_sigint`) is registered as a closure capturing the
  current `RunContext`, rather than reading a module global.
- Tests construct an isolated `RunContext` instead of monkeypatching globals — the
  save/restore `try/finally` goes away.

The `dataclass` shape is a proposal; the contract is "one owner, explicit
threading, zero mutable module-level lifecycle globals."

## Order — why tests first

`_handle_sigint`, force-quit, and the run loop are signal handling and
child-process killing — the most dangerous code in a tool that runs against every
project. Refactoring it **before** a characterization test grid is refactoring
blind.

That net exists today. `tests/test_runtime.py` covers `_run_summary`,
`_fmt_elapsed`, `_with_caffeinate`, and `_handle_sigint`, including both of its
force-quit branches; `tests/test_agents.py` covers sidecar session I/O and
`kill_active_child`. These tests pin today's behaviour — signals, elapsed time, the
force-quit notification, child-process teardown — so `RunContext` can be
introduced under their protection, with the guarantee that behaviour hasn't moved.

What stands between this doc and the work is therefore a decision to do it, not a
missing precondition.

## What it touches

`state.py` (goes away or shrinks a lot), `main.py` (creating and threading the
context), `runtime.py` (lifecycle helpers take the context), `agents.py`
(`_run_claude`/`kill_active_child` stop writing to a global — the process goes into
the context or is passed explicitly). Boundaries are drawn by state ownership, not
by line count.

## Definition of done

- Zero mutable module-level lifecycle globals in `state.py`.
- The runtime/sidecar tests stay green **without** save/restore boilerplate — they
  build a `RunContext` directly.
- Behaviour byte-for-byte: the same console output, the same signals, the same
  force-quit notification, the same child-process teardown.
