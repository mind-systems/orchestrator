# Phase sessions and token cost

`enable_phase_sessions` controls whether the `PlannerReviewer` session carries over between tasks within one roadmap phase. Default: `false`.

The orchestrator groups tasks into phases — any `##` or `###` heading in the roadmap marks a phase boundary. Within one phase, `PlannerReviewer` holds one Claude session: each next task continues it via `--resume` instead of starting fresh, so by the third task of a phase the planner already knows `ARCHITECTURE.md` and the context of earlier plans without re-reading it. The session resets at the phase boundary, and it lives only in the memory of the current process — if the orchestrator restarts mid-phase, the next task starts with a clean session, with no loss of correctness. When `enable_phase_sessions` is `false`, the orchestrator does not pass the `PlannerReviewer` session ID between tasks even within one phase — every task starts with a fresh session, which makes it possible to compare token cost on an identical run with and without phase sessions. This page explains why `false` is the default: what was measured, and what follows from it.

## The question

A carried-over session is meant as cross-task memory: by the third task, the planner remembers the context of earlier plans and does not re-read it. Two hypotheses about its cost:

1. Carrying the session over saves tokens (less context re-reading).
2. If it does not save tokens, the cost is in `--resume` itself: every return to a session re-reads a growing transcript. The fix would then be to keep one agent process alive through the whole phase and stream prompts into it, rather than restarting `claude --resume` on every turn.

Both are tested by measurement.

## Measurement: resume vs. a live process

A controlled test with byte-identical prompts across two invocation modes of the same session:

- **resume** — the process dies between turns; each turn is picked back up via `claude --resume <sid>`;
- **live** — one `claude -p --input-format stream-json` process lives between turns, prompts go to its stdin.

Each mode ran with a 0-second pause and a 6.5-minute pause between turns (simulating other agents working in the pipeline). The metric is the second turn's input-token breakdown: `cache_read` (read from cache, ~10% of price) vs. `cache_creation` (write to cache, ~125%).

| Mode | input | cache_creation | cache_read |
|---|---|---|---|
| resume, no pause | 10 | 319 | 37161 |
| live, no pause | 10 | 340 | 37202 |
| resume, 6.5 min pause | 10 | 80 | 37202 |
| live, 6.5 min pause | 10 | 335 | 37202 |

Conclusion: `cache_read` is identical across all four cells, including `resume` after the pause. That means:

- Claude Code's prompt cache survives a pause of several minutes (an extended TTL is in play, not the default 5 minutes), so `--resume` fully reuses the cached prefix.
- **A live process saves no tokens at all** compared to `--resume`. The API is stateless: the full history is sent on every turn in both modes, and only the server-side cache — pinned to wall-clock TTL, not to the process's lifetime — makes the repeat send cheaper.

A live process only saves local cost — process spawn, re-reading the transcript from disk, MCP reconnection. That is latency and CPU, not tokens.

## Measurement: a phase session vs. a fresh one per task

A run of one phase (7 tasks) with `enable_phase_sessions: true` costs roughly twice as much against the 5-hour budget as with `false`.

The cause is not "cold" re-reading, but **the volume of warm `cache_read` in a growing prefix**. With the carried-over session enabled, by the last task the planner's prefix drags along every earlier plan, review, and tool output. Every turn re-reads that whole prefix — at the cheap cache-read rate, but the volume accumulates super-linearly with the number of tasks. With a fresh session, every task starts with a small prefix.

This is the same reason a live process does not help: it would reuse the same growing prefix at the same rate.

## Quality

Runs with phase sessions enabled show no measured gain in quality or speed. Two runs with the flag enabled varied in duration from each other more than an enabled run varies from a disabled one — the spread from model non-determinism outweighs the flag's effect. The test phase consisted of small, loosely coupled tasks (each its own file from a self-contained note), where cross-task memory is barely needed.

## When to enable

The default, `false`, is half the cost with no quality loss on typical phases.

`true` is worth considering only for tightly coupled phases, where an early task's decision non-obviously constrains a later one and the chain of reasoning matters, not just its conclusion. Even there, passing context through a brief file summary is cheaper: every plan and review already sits in `.ai-factory/`, and the planner reads them on demand. A session carries the raw conversation; files carry conclusions — conclusions are usually enough for quality.
