# Usage limits

## Thresholds

Before each task, the orchestrator runs `claude /usage` and checks two independent thresholds from that one call. Exceeding either halts the run before the next task starts; see [outcomes.md](../concepts/outcomes.md) for what a halt is. Default values and overlay rules live in [configuration.md](../reference/configuration.md).

| Threshold | Config key | Scope |
|---|---|---|
| Session | `usage_threshold_5h` | The current 5-hour Claude session |
| Weekly | `usage_threshold_weekly` | Usage across all models over the week |

## Log line

A log line precedes each task, showing the accumulation trend:

```
  [usage: session 26% · week 52%]
```

## When `/usage` cannot be parsed

If `claude /usage` is unavailable or its output fails to parse, a warning is logged and the run continues. The weekly threshold is checked independently of the session threshold from the same output; if that output carries no weekly figure, the weekly threshold is skipped.
