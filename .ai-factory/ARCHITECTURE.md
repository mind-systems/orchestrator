# Architecture: Ports and Adapters

## Overview

One task pipeline runs unchanged for every mode. What differs between modes is an implementation chosen where the run is assembled, never a question the pipeline asks. Dependency inversion is the one structural rule: the flow depends on what a step does, and the implementation that does it is supplied from outside.

Packaging comes second: modules are cut by concern, one small module per concern, and the folder structure below records that cut. What each stage of the pipeline does is described in [Pipeline](../docs/pipeline.md).

## The one flow

`process_task` in `pipeline.py` is the single pipeline: plan, plan review, implement, verify, mark done and commit. It never asks which mode it runs in; everything that differs arrives as a value or an implementation handed to it.

## What varies

- **Mode**, implement vs test. The `Mode` record, defined in `pipeline.py`, holds a mode's own static values — its roadmap file, planner prompt, header and skip wording — and one verify kind, and has two instances, `IMPLEMENT_MODE` and `TEST_MODE`. The choice is made at the composition root.
- **Verify step**, a port named `VerifierProtocol`. Given the plan and the output path, an implementation writes the verify artifact and reports pass or fail by that artifact's completion signal. There are two implementations: code review by `PlannerReviewer`, in the planner's own session, and the test run by `TestRunner`, with no LLM. The port and the kind type live in `ports.py`; the kind is one record, `VerifyKind`, whose instances `REVIEW_VERIFY` and `TEST_RUN_VERIFY` sit beside their implementations in `agents.py`. The kind holds everything that depends on that choice: the step's name in the sidecar, its failure tag, the artifact directory and suffix, the pass signal, the wording the run prints, and the factory that builds the implementation for a task. Each implementation reads its own pass signal from its kind. There are two kinds, review and test run. The choice is made at the composition root and carried on the mode record.
- **Layout**, the default flat roadmap pair vs a named roadmap. This is a value, not a port: the per-roadmap artifact subdirectory, derived once from the roadmap path at assembly, from which every artifact directory derives in one place. See [Named roadmaps](../docs/features/named-roadmaps.md).
- **Agent roles**. Three LLM roles — `PlannerReviewer`, `PlanReviewer` and `Implementer` — run over one runner, `_run_claude` in `claude_cli.py`. They differ in prompt, tool list and session policy, and they are not interchangeable, so they share a runner, not a port. `TestRunner` is not a role; it is the second verify implementation.

## Composition root

`_implement_loop` and `_test_loop` in `main.py` assemble the mode record — roadmap path, artifact subdirectory, planner prompt, verify kind — and hand it to the one flow. They are the only place that knows which implementation runs.

## The rule

A new difference between modes or roles is a new implementation chosen at the composition root, never a branch inside the flow. A kind that gains a second member is named here as a port, judged by how many places must change to add a third. A choice is held once: what depends on it lives in the same record or derives from it, never beside it as a second value that must agree.

## Invariants

- Step values and resume: [Resume](../docs/features/resume.md)
- The file protocol and completion signals: [Pipeline](../docs/pipeline.md)
- Outcomes: [Outcomes](../docs/concepts/outcomes.md)
- Escalation: [Escalation](../docs/features/escalation.md)

## Folder Structure

```
orchestrator/
├── orchestrator/
│   ├── __init__.py      # Package marker
│   ├── main.py          # Composition root: CLI, _implement_loop, _test_loop
│   ├── pipeline.py      # The flow: process_task, Mode and its instances, the roadmap loop, _artifact_dir, the commit step
│   ├── resume.py        # The flow: step detection
│   ├── agents.py        # Roles: the LLM roles, TestRunner, the verify kinds' instances
│   ├── claude_cli.py    # Adapter: resolving and launching the claude CLI, killing the active child, result classification, retries
│   ├── layout.py        # Adapter: named-roadmap resolution at assembly
│   ├── usage.py         # Adapter: usage-threshold gating (/usage parse, session/weekly limits)
│   ├── notify.py        # Adapter: Telegram alerts
│   ├── runtime.py       # Adapter: signals, caffeinate
│   ├── errors.py        # Vocabulary: the outcome exceptions
│   ├── protocol.py      # Vocabulary: the file protocol — sidecar read/write, completion-signal and escalation recognition
│   ├── ports.py         # Vocabulary: VerifierProtocol and the VerifyKind type
│   ├── roadmap.py       # Vocabulary: ROADMAP.md parsing, mark_done()/mark_skipped()
│   ├── config.py        # Vocabulary: config load + validation (global base + per-project overlay)
│   ├── state.py         # Vocabulary: shared mutable process state for one run
│   └── prompts/         # Static system prompts (data, not code)
│       ├── planner.md
│       ├── reviewer.md
│       ├── implementer.md
│       ├── escalation.md
│       └── test-planner.md
├── .ai-factory/         # AI context (not source code)
├── docs/
├── pyproject.toml
└── CLAUDE.md
```

## Dependency Rules

Imports point downward only: no cycles, nothing imports `main`, and each module holds one concern. The layers, top to bottom:

| Layer | Modules |
|---|---|
| Composition root | `main.py` |
| The flow | `pipeline.py`, `resume.py` |
| Roles and adapters | `agents.py`, `claude_cli.py`, `layout.py`, `usage.py`, `notify.py`, `runtime.py` |
| Vocabulary | `errors.py`, `protocol.py`, `ports.py`, `roadmap.py`, `config.py`, `state.py` |

- ✅ A module imports from layers below its own, and within a layer only along these named edges:
  - the flow: `pipeline` → `resume`
  - roles and adapters: `agents` → `claude_cli`, `usage` → `claude_cli`, `runtime` → `claude_cli`, `runtime` → `notify`
- ✅ The vocabulary imports nothing from the package at runtime; a type-only import under `TYPE_CHECKING` may reach another vocabulary module, never a layer above. A type annotation is still an edge
- ✅ Edges are stated as directions, never as inventories of the symbols one module takes from another

## Anti-Patterns

- ❌ Passing data between agents via Python variables — files only
- ❌ Step-selection logic in the roles — it belongs in the flow
- ❌ Launching the `claude` CLI anywhere but `claude_cli.py` — the flow reaches it only through the roles in `agents.py`
- ❌ Reading/writing `ROADMAP.md` from the roles — only the flow, via `roadmap.py`

## Features (roadmap-prune v2)

| Feature | Hashes |
|---------|--------|
| **Pipeline control** | |
| Iterative plan review gate | 15f1e77 |
| Crash recovery — mid-task resume | 48e435d de7849d |
| Test mode — real test runner gate | fb219a4 |
| Dynamic roadmap re-scan loop | a9b1c12 |
| Roadmap breakpoint marker | 9a4aa63 |
| Auto-push to remote after task | e50159f |
| **Session & observability** | |
| Phase-persistent planner session | 025658d |
| Per-task usage guard | b214041 |
| Telegram alerts — colour-coded outcomes | a3ceb9b b71a648 |
| Deferred-observations review channel | c93582e |
| **Configuration** | |
| Project-root config file | 992a38e |
| **Multiuser** | |
| Named per-developer roadmaps | 5d2ff7f |
| **Internal** | |
| Roadmap drop history | 282007d, 2d4789b |
