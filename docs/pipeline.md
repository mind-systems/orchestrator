# Pipeline

## The agent pipeline

Every task goes through two phases, each bounded by the same iteration limit.

The plan phase runs first: `PlannerReviewer` explores the codebase and writes a plan. `PlanReviewer` checks it and writes the result to `.ai-factory/plan-reviews/` — ending with `PLAN_REVIEW_PASS`, or a description of the problems. If the plan does not pass, the planner reads the review file and rewrites the plan. The cycle repeats up to `max_iterations` times (set in [configuration.md](reference/configuration.md)).

Once the plan is approved, the implement phase begins: the implementer writes code, `PlannerReviewer` reviews the changes and writes the result to `.ai-factory/reviews/`. If problems are found, the path to the review file is passed to the implementer as an explicit parameter; it reads the file and applies fixes, and review repeats. The limit is the same, `max_iterations`. Exhausting the limit in either phase without a PASS signal is a task failure (see [outcomes.md](concepts/outcomes.md)).

## Agent sessions

| Agent | Model | Effort | Session |
|---|---|---|---|
| PlannerReviewer | Opus | high | Persistent within a task and within a phase |
| PlanReviewer | Opus | high | Fresh on every attempt |
| Implementer | Sonnet | high | Persistent within a task |
| TestRunner | — | — | None (a shell executor) |

Models are fixed in code and are not configurable through the settings file.

Planner and reviewer are one agent (`PlannerReviewer`), running in a single Claude session via `--resume`. This means the reviewer knows the entire planning context — it understands not only what was written but why. The implementer also keeps its session open across the iterations of the fix cycle, accumulating the context of its own fixes.

`PlanReviewer` is a separate agent with a clean session on every attempt. This is deliberate: it looks at the plan without the author's own bias, as an independent reviewer.

`PlannerReviewer`'s session also persists across a whole roadmap phase — see [phase-sessions.md](features/phase-sessions.md) for the phase boundary, the reset behaviour, and why the default disables carrying it forward.

Every time an agent runs, its session ID is printed to the log — visible right after the `--- Claude agent (...) ---` line. That identifier locates the session's own file under `~/.claude/projects/` for diagnosis.

## The file protocol

Agents never communicate directly — only through files in the target project's `.ai-factory/`. The planner writes the plan, the implementer reads it. `PlanReviewer` writes the plan review to `plan-reviews/`, the planner reads it on the next attempt. The reviewer writes the code review to `reviews/`, and the path to that file is passed to the implementer as an explicit parameter on the next iteration. The orchestrator coordinates the call order and watches for signals (`PLAN_REVIEW_PASS`, `REVIEW_PASS`, `ESCALATION`).

Artifact directory layout and per-roadmap routing live on [named-roadmaps.md](features/named-roadmaps.md); resume state built on top of this protocol lives on [resume.md](features/resume.md).

## Completion signals

Every agent uses the same protocol: it writes its result to a file, and puts a signal as the file's last line if all is well — or leaves the file without one if problems remain. `PlanReviewer` writes `PLAN_REVIEW_PASS`, the reviewer writes `REVIEW_PASS`. The orchestrator reads the file, counts iterations, and decides whether to continue or to stop and show the last review to the user.

Any of the four roles may instead write `ESCALATION` as that last line — see [escalation.md](features/escalation.md) for what it means and what it requires.

A review file may carry a `## Deferred observations` section before the signal line — a non-blocking channel for observations that are verified but deliberately not blocking, outside the task's own scope. This section's presence does not affect PASS/FAIL: the orchestrator still determines the outcome only from the file's last line.
