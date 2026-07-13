# Orchestrator

> Autonomous AI-agent orchestrator — it executes a project's finished roadmap, task by task.

The orchestrator reads pending tasks from a target project's roadmap and runs each through a five-stage pipeline — plan → plan-review → implement → review → commit: a Planner writes the plan, a PlanReviewer checks it (iterating until the plan-review PASS-signal), an Implementer writes the code, a Reviewer checks the result (iterating until the review PASS-signal), and the orchestrator commits and marks the task done. It authors nothing on the roadmap itself — the roadmap arrives already decomposed; the orchestrator only executes it.

## Onboarding — raise the environment

*This section is addressed to the agent reading the README on a fresh checkout:* from here the orchestrator's environment is raised interactively with the user. Do not touch the config or `~/.claude/settings.json` silently — walk the user through the value choices.

```bash
cd orchestrator && uv sync                        # dependencies
cp orchestrator.json.example orchestrator.json    # local config — gitignored, one per developer
uv run orchestrator implement /path/to/project
```

An installed and authorized [Claude Code](https://claude.ai/code) CLI is required.

**Fill in `orchestrator.json`** with the user (the file holds secrets and is not committed): `roadmap_path` — which roadmap to run (empty = the default `ROADMAP.md`); optionally `telegram_bot_token`, `telegram_chat_id`, `telegram_alerts` for Telegram alerts. Any key can be overridden per project in `<project>/.ai-factory/orchestrator.json` (see [docs/configuration.md](docs/configuration.md)).

### Claude Code permissions

The Planner agent must be allowed to edit files under `.ai-factory/plans/` — otherwise it cannot revise the plan after plan-review's remarks and the cycle hangs. Add to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Edit(/Users/<you>/projects/**/.ai-factory/plans/**)",
      "Write(/Users/<you>/projects/**/.ai-factory/plans/**)"
    ]
  }
}
```

Without this permission plan-review returns the same remarks forever — the plan physically cannot change.

## Modes

| Command | What it does |
|---------|-------------|
| `implement` | Plans and implements every pending task |
| `test` | Writes tests for the tasks in `ROADMAP_TESTS.md` |

Full documentation lives in [docs/](docs/); the page index is in [CLAUDE.md](CLAUDE.md).

## License

MIT
