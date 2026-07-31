# Resume after an interruption

## Detecting where to continue

If the orchestrator is interrupted mid-task (timeout, Ctrl+C, a network failure), the next run automatically determines which step to continue from — no manual intervention required.

## What the sidecar holds

Each time a phase completes, the orchestrator writes its name to a JSON sidecar next to the plan, sharing its stem: `.ai-factory/plans/{NN}-{slug}.json` (for a named roadmap: `.ai-factory/plans/{roadmap-slug}/{NN}-{slug}.json` — see [named-roadmaps.md](named-roadmaps.md) for the directory-routing rule). The sidecar holds `step` (the current phase), the planner's and implementer's session IDs (for resume via `--resume`), accumulated elapsed time, and — if the run has escalated — an escalation record: which role raised it and where its artifact lives (see [escalation.md](escalation.md)). On the next run, the orchestrator reads `step` and jumps straight to the right phase, without repeating what is already done.

## `step` values

The `:N` suffix is the iteration number. `plan_reviewed` and `escalated` are the only unindexed markers.

| `step` value | Meaning | What resume does |
|---|---|---|
| `planned:N` | Round N's plan is ready; no verdict yet | Resumes the plan review at iteration N, without re-running the planner |
| `plan_review_failed:N` | Round N's plan review failed | Marks which attempt to resume from |
| `plan_reviewed` | The plan passed review | Implementation may begin |
| `implemented:N` | Round N's code is ready; no verdict yet | Resumes the verify step at iteration N, without re-running the implementer |
| `review_failed:N` | Round N's code review failed | Marks which attempt to resume from |
| `test_run_failed:N` | Round N's test run failed (test mode) | Marks which attempt to resume from |
| `escalated` | The run escalated; implies no next attempt | Stops again immediately, the same way it stopped the first time, and waits for a human decision rather than retrying |

If `step` references a file that is not on disk (for example, after `/task-rescue` deletes a plan review), the value is ignored and the orchestrator falls back to detecting the step heuristically from whatever artifacts are on disk.

## Plan selection

Plan selection for resume relies on the artifact file protocol: a committed and clean (tracked+clean) plan file is treated as belonging to an already-completed task and is skipped — only an uncommitted (in-flight) plan is picked up. If a developer manually commits the artifacts of an unfinished task, this leads to re-planning, not a false completion.
