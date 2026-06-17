# Config file — replace env vars with explicit config

**Date:** 2026-06-17
**Source:** conversation context

## Key Findings

- All orchestrator settings live in `~/.orchestrator.json` — one file, read automatically at startup
- No hardcoded fallbacks anywhere in code — missing file or missing key = error, not silent default
- `ORCHESTRATOR_CONFIG` env var overrides the default path (single meta-env-var, not settings)
- Config is loaded once in `cli()` and passed as a dataclass to all functions that need it
- Removes all five `os.environ.get("ORCHESTRATOR_*", ...)` call sites

## Details

### Config file format

`~/.orchestrator.json`:
```json
{
  "max_iterations": 3,
  "usage_threshold_5h": 90,
  "usage_threshold_weekly": 95,
  "enable_phase_sessions": true
}
```

All four fields are required. The file must exist. Any missing field is an error at startup.

Note: `usage_threshold_5h` is not a valid Python identifier, so the dataclass field is named
`usage_threshold_5h`. The mapping happens once in `load_config()`.

### New module: `orchestrator/config.py`

```python
from dataclasses import dataclass
from pathlib import Path
import json, os

@dataclass
class OrchestratorConfig:
    max_iterations: int
    usage_threshold_5h: float      # JSON key: "usage_threshold_5h"
    usage_threshold_weekly: float
    enable_phase_sessions: bool

def load_config() -> OrchestratorConfig:
    path = Path(os.environ.get("ORCHESTRATOR_CONFIG", "~/.orchestrator.json")).expanduser()
    if not path.exists():
        raise SystemExit(
            f"Config file not found: {path}\n"
            f"Create it with all required fields:\n"
            f'{{"max_iterations": 3, "usage_threshold_5h": 90, "usage_threshold_weekly": 95, "enable_phase_sessions": true}}'
        )
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(f"Config file is not valid JSON: {path}\n{e}")

    required = ["max_iterations", "usage_threshold_5h", "usage_threshold_weekly", "enable_phase_sessions"]
    for key in required:
        if key not in data:
            raise SystemExit(f"Missing required key '{key}' in {path}")

    return OrchestratorConfig(
        max_iterations=int(data["max_iterations"]),
        usage_threshold_5h=float(data["usage_threshold_5h"]),
        usage_threshold_weekly=float(data["usage_threshold_weekly"]),
        enable_phase_sessions=bool(data["enable_phase_sessions"]),
    )
```

### Changes in `main.py`

Call `load_config()` at the top of `cli()` — before argument parsing, before any agent work.
Pass `config` to `run_implement()`, `run_test()`, then down to `_implement_loop()`,
`_test_loop()`, `process_milestone()`, `process_test_milestone()`, `_check_usage_limits()`.

Replace all five `os.environ.get("ORCHESTRATOR_*", ...)` calls with `config.*` field reads:

| Old | New |
|-----|-----|
| `int(os.environ.get("ORCHESTRATOR_MAX_ITERATIONS", "3"))` | `config.max_iterations` |
| `float(os.environ.get("ORCHESTRATOR_USAGE_THRESHOLD", "90"))` | `config.usage_threshold_5h` |
| `float(os.environ.get("ORCHESTRATOR_WEEKLY_THRESHOLD", "95"))` | `config.usage_threshold_weekly` |
| `os.environ.get("ORCHESTRATOR_PHASE_SESSIONS", "true").lower() != "false"` | `config.enable_phase_sessions` |

### Error messages

- File not found → print example JSON and exit 1
- Invalid JSON → print parse error and exit 1
- Missing key → name the exact key and exit 1

### CLAUDE.md update

Add to the Commands section:
```
# Config file (required before first run)
cat > ~/.orchestrator.json << 'EOF'
{
  "max_iterations": 3,
  "usage_threshold_5h": 90,
  "usage_threshold_weekly": 95,
  "enable_phase_sessions": true
}
EOF
```

### docs/configuration.md update

Full rewrite — replace "Переменные окружения" with "Файл конфигурации". Structure:
- Required JSON file at `~/.orchestrator.json`, all four fields mandatory
- Single env var `ORCHESTRATOR_CONFIG` to override path — no per-setting env vars
- One subsection per field: `max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`
- `usage_threshold_5h` subsection includes the `[usage: session N% · week N%]` log line example
- Agent models table unchanged, update the `enable_phase_sessions` reference in the PlannerReviewer note

### docs/how-it-works.md update

Four lines reference the removed env vars — reword each to use the config field name:

- L7: `Цикл повторяется до ORCHESTRATOR_MAX_ITERATIONS раз.` → `Цикл повторяется до \`max_iterations\` раз (задаётся в \`~/.orchestrator.json\`).`
- L9: `Лимит тот же — ORCHESTRATOR_MAX_ITERATIONS.` → `Лимит тот же — \`max_iterations\`.`
- L35: `Переменная ORCHESTRATOR_PHASE_SESSIONS=false отключает carry-forward…` → `Поле \`enable_phase_sessions: false\` в конфиге отключает carry-forward…`
- L39: `…сессионный (ORCHESTRATOR_USAGE_THRESHOLD, по умолчанию 90%) и недельный … (ORCHESTRATOR_WEEKLY_THRESHOLD, по умолчанию 95%)…` → `…сессионный (\`usage_threshold_5h\`, по умолчанию 90) и недельный (\`usage_threshold_weekly\`, по умолчанию 95)…`

### README.md update

L48 in the docs table: change `Env-переменные, модели агентов, лимиты итераций` → `Файл конфигурации, модели агентов, лимиты итераций`.

### .ai-factory/DESCRIPTION.md update

Two lines reference `ORCHESTRATOR_MAX_ITERATIONS` — reword to the config field:

- L10: replace `configurable via \`ORCHESTRATOR_MAX_ITERATIONS\`` → `configurable via \`max_iterations\` in \`~/.orchestrator.json\``
- L59: replace `\`ORCHESTRATOR_MAX_ITERATIONS\` env var (default 3) — single iteration limit for all flows` → `\`max_iterations\` field in \`~/.orchestrator.json\` (default 3) — single iteration limit for all flows`

### Files to touch

- `orchestrator/config.py` — new file
- `orchestrator/main.py` — import `load_config`, call in `cli()`, thread through call chain, remove 5 env reads
- `CLAUDE.md` — add config setup to Quick Start
- `docs/configuration.md` — replace env vars section
- `docs/how-it-works.md` — reword 4 env-var references (L7, L9, L35, L39)
- `README.md` — update L48 doc-table label
- `.ai-factory/DESCRIPTION.md` — update L10 and L59
