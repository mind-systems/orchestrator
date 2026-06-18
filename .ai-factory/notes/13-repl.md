# Interactive REPL mode

**Date:** 2026-06-17
**Source:** conversation context

## Key Findings

- Bare `uv run orchestrator` opens an interactive session; subcommand invocations (`implement <path>`, `test <path>`) still work unchanged
- Config loaded from file at startup, displayed on entry; `set` mutates in-session copy, `save` persists to the same file
- `readline` (stdlib) provides history and line editing — zero new dependencies
- New module `orchestrator/repl.py`; `cli()` in `main.py` routes to `run_repl(config, config_path)` when no subcommand given

## Details

### Entry point change in `main.py`

`cli()` currently defaults to `implement` on current dir when no subcommand is given. Change: when `args.command` is `None` (no subcommand), call `run_repl(config, config_path)` instead. Subcommands `implement` and `test` with explicit path arguments still work as before.

`config_path` is the resolved `Path` used by `load_config()` — pass it through so `save` knows where to write.

### New module: `orchestrator/repl.py`

```python
import readline  # activates line editing and history automatically
from pathlib import Path
import json, os
from .config import OrchestratorConfig

FIELD_TYPES = {
    "max_iterations": int,
    "usage_threshold_5h": float,
    "usage_threshold_weekly": float,
    "enable_phase_sessions": lambda v: v.lower() not in ("false", "0", "no"),
}

def run_repl(config: OrchestratorConfig, config_path: Path) -> None:
    # mutable working copy
    settings = {
        "max_iterations": config.max_iterations,
        "usage_threshold_5h": config.usage_threshold_5h,
        "usage_threshold_weekly": config.usage_threshold_weekly,
        "enable_phase_sessions": config.enable_phase_sessions,
    }
    _print_welcome(settings, config_path)
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        _dispatch(line, settings, config_path)

def _dispatch(line, settings, config_path):
    parts = line.split(None, 2)
    cmd = parts[0].lower()

    if cmd in ("exit", "quit"):
        raise SystemExit(0)

    elif cmd == "help":
        print(_HELP)

    elif cmd == "show":
        for k, v in settings.items():
            print(f"  {k:<28} {v}")

    elif cmd == "set":
        if len(parts) < 3:
            print("Usage: set <key> <value>")
            return
        key, raw = parts[1], parts[2]
        if key not in FIELD_TYPES:
            print(f"Unknown key '{key}'. Known: {', '.join(FIELD_TYPES)}")
            return
        try:
            value = FIELD_TYPES[key](raw)
        except (ValueError, TypeError):
            print(f"Invalid value '{raw}' for {key}")
            return
        old = settings[key]
        settings[key] = value
        print(f"  {key}: {old} → {value}")

    elif cmd == "save":
        tmp = config_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(settings, indent=2))
        os.replace(tmp, config_path)
        print(f"  Saved to {config_path}")

    elif cmd == "implement":
        if len(parts) < 2:
            print("Usage: implement <path>")
            return
        _run_pipeline(parts[1], settings, mode="implement")

    elif cmd == "test":
        if len(parts) < 2:
            print("Usage: test <path>")
            return
        _run_pipeline(parts[1], settings, mode="test")

    else:
        print(f"Unknown command '{cmd}'. Type 'help'.")
```

### `_run_pipeline` inside REPL

Builds an `OrchestratorConfig` from current `settings` dict, then calls `run_implement()` or `run_test()` from `main.py`. The existing SIGINT handler (`_handle_sigint` + `_state.stop_requested`) applies unchanged — Ctrl+C during a pipeline run stops the run and returns to the REPL prompt.

```python
from .config import OrchestratorConfig
from .main import run_implement, run_test

def _run_pipeline(path_str, settings, mode):
    from pathlib import Path
    cfg = OrchestratorConfig(**settings)
    project_dir = Path(path_str).expanduser().resolve()
    if not project_dir.exists():
        print(f"Path not found: {project_dir}")
        return
    if mode == "implement":
        run_implement(project_dir, cfg)
    else:
        run_test(project_dir, cfg)
```

### Welcome screen

```
Orchestrator  •  config: ~/.orchestrator.json

  max_iterations          3
  usage_threshold_5h      90
  usage_threshold_weekly  95
  enable_phase_sessions   true

Type 'help' for commands.
```

### Help text

```
Commands:
  implement <path>      Run implement pipeline on target project
  test <path>           Run test pipeline on target project
  set <key> <value>     Change a setting for this session
  show                  Show current settings
  save                  Write current settings to config file
  help                  Show this message
  exit                  Exit (also Ctrl+D)
```

### Guards

- `set enable_phase_sessions` accepts `true/false`, `1/0`, `yes/no` (case-insensitive)
- `save` uses tmp + `os.replace` (atomic, same pattern as `_write_session`)
- Unknown key in `set` → named error, no crash
- Invalid type in `set` → named error, no crash
- Ctrl+C at the `>` prompt → clean exit (same as `exit`)
- Ctrl+C during pipeline → stops pipeline, returns to `>` prompt (existing SIGINT handler)
- Empty input line → ignored, re-prompt

### Files to touch

- `orchestrator/repl.py` — new file, all REPL logic
- `orchestrator/main.py` — route `args.command is None` to `run_repl(config, config_path)`; pass `config_path` out of `load_config()` (currently returns only `OrchestratorConfig` — change return to `tuple[OrchestratorConfig, Path]` or store path on the config object)
- `CLAUDE.md` — add `uv run orchestrator` (no args) → opens REPL to Commands section
- `docs/workflow.md` — mention REPL as the interactive entry point
