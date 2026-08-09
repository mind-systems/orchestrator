# Configuration

## Configuration file

All orchestrator settings are set in `orchestrator.json` at the repository root. The file is mandatory — the orchestrator will not start without it. It is gitignored, so setting changes never show up in `git diff`; the template to copy from is `orchestrator.json.example`.

```json
{
  "max_iterations": 3,
  "usage_threshold_5h": 90,
  "usage_threshold_weekly": 95,
  "enable_phase_sessions": false
}
```

All four fields are mandatory. A missing file, or a missing field, is a startup error with a clear message.

The file's path can be overridden through an environment variable:

```bash
ORCHESTRATOR_CONFIG=/path/to/my-config.json uv run orchestrator implement /path/to/project
```

## Settings keys

| Key | Default | Meaning |
|---|---|---|
| `max_iterations` | `3` | The iteration limit for every cycle — plan review, code review, and test run. See [pipeline.md](../pipeline.md). |
| `usage_threshold_5h` | `90` | The 5-hour session usage threshold. See [usage-limits.md](../features/usage-limits.md). |
| `usage_threshold_weekly` | `95` | The weekly usage threshold across all models. See [usage-limits.md](../features/usage-limits.md). |
| `enable_phase_sessions` | `false` | Whether the `PlannerReviewer` session carries over between tasks within a phase. See [phase-sessions.md](../features/phase-sessions.md). |
| `roadmap_path` | absent | Which roadmap the orchestrator reads. See [named-roadmaps.md](../features/named-roadmaps.md). |

## Per-project overlay

The global `orchestrator.json` sets the settings for the whole fleet — they apply to every target project alike. A project overrides the settings it needs with its own `<project>/.ai-factory/orchestrator.json` file, layered **on top of** the global base.

Priority, lowest to highest:

1. `OrchestratorConfig`'s own defaults (for optional keys).
2. The global `orchestrator.json` (or the path from `ORCHESTRATOR_CONFIG`) — the base.
3. `<project>/.ai-factory/orchestrator.json` — the project overlay.

The overlay is **partial**: a project names only the keys it wants to change — it does not need to repeat the whole set. The base's four mandatory keys (`max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`) are **not** mandatory in the overlay — the base has already supplied and validated them. Keys absent from the overlay are inherited from the base; keys present in it win.

Example — a project needs 5 iterations instead of the global 3:

```json
{ "max_iterations": 5 }
```

Everything else comes from the global config.

Merge rules:

- The merge is **shallow**: `telegram_alerts` in the overlay **replaces** the base's list wholesale, it does not union with it.
- The overlay's `roadmap_path` goes through the same guard (a relative path, no `..` segment) and the same three-state resolver as the global one — see [named-roadmaps.md](../features/named-roadmaps.md).
- Broken overlay JSON is a startup error naming the overlay file's path.
- **The absence of an overlay file is byte-stable**: a project without one behaves exactly as before, to the byte.

The orchestrator's overlay lives in its own `orchestrator.json` inside the project's `.ai-factory/`.

## Telegram notifications

Optional fields for sending Telegram notifications when the orchestrator halts, a task completes, or the whole run finishes:

```json
{
  "telegram_bot_token": "1234567890:AAF...",
  "telegram_chat_id": "-1001234567890",
  "telegram_alerts": ["task-fail", "stop", "task", "done"]
}
```

`telegram_bot_token` and `telegram_chat_id` are the bot's credentials. If either is empty or absent, notifications are not sent (a silent no-op, not an error).

`telegram_alerts` is the list of event types to notify on. What each colour says lives in [fault-handling.md](../concepts/fault-handling.md)'s own table:

| Type | Colour |
|---|---|
| `task-fail` | 🔴 |
| `stop` | 🟡 |
| `escalation` | 🔵 |
| `task` | 🟢 |
| `done` | 🟢 |

The `stop` token denotes an operational halt, so an alert list carried over from an older configuration is worth re-checking against the current table.

An empty list, `[]`, disables all notifications even with credentials filled in. A network error on send does not stop the run — see [fault-handling.md](../concepts/fault-handling.md) for what happens to the alert itself.
