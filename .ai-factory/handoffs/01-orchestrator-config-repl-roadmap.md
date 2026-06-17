# Handoff — orchestrator-config-repl-roadmap

## 1. Frame
We spent the session designing and documenting new orchestrator features (usage guard, phase sessions, config file, REPL) and adding them to the roadmap — the chat is compacted but the knowledge is durable in files; rehydrate from them, don't trust memory.

## 2. Read-first map

### Must-read now (minimal rehydration set)
- `.ai-factory/ROADMAP.md` — full task list; bottom of file has the pending milestones in `## Next` section
- `.ai-factory/notes/12-config-file.md` — spec for the config file milestone (most recent, most detailed)
- `docs/configuration.md` — already updated to target state (3D docs); reflects what the config file milestone must implement

### Read on demand
- `.ai-factory/notes/09-adaptive-usage-guard.md` — original adaptive UsageGuard design (superseded by note 11)
- `.ai-factory/notes/10-phase-session-persistence.md` — phase session spec (`section` field on `Milestone`, `phase_session_id` threading)
- `.ai-factory/notes/11-usage-guard-and-phase-session-config.md` — per-milestone usage check + `ORCHESTRATOR_PHASE_SESSIONS` (already implemented)
- `orchestrator/agents.py` — `_has_signal()` helper added this session (lines 25-28); `_read_sessions`, `_write_session` sidecar helpers
- `orchestrator/main.py` — `_check_usage_limits()` called before every milestone; inline loops in `_implement_loop` and `_test_loop` thread `phase_session_id`
- `docs/how-it-works.md` — updated with phase session and usage guard sections
- `docs/target-project.md` — updated with Phases section

## 3. Current state

**Done:**
- `_has_signal(text, signal)` helper in `agents.py` — replaces `endswith()` for REVIEW_PASS / PLAN_REVIEW_PASS detection; scans last 5 lines for exact-match line; handles stray `</content>` XML tags and is stricter against false positives
- Per-milestone usage check (`_check_usage_limits()`) — checks both session (5h) and weekly thresholds before every milestone, logs `[usage: session N% · week N%]`
- Phase-persistent PlannerReviewer sessions — `Milestone.section` field, inline loops carry `phase_session_id`, reset at `##`/`###` boundaries
- `ORCHESTRATOR_PHASE_SESSIONS` env var (now to become config field `enable_phase_sessions`)
- `docs/configuration.md` — fully rewritten to target state: config file-based, no env vars per setting, all four fields documented
- `docs/how-it-works.md`, `docs/target-project.md` — updated
- Roadmap tasks added and noted for: robust signal detection, per-milestone usage check, phase sessions, config file, REPL (last two pending)

**In-flight (pending roadmap milestones, not yet implemented):**
- **Config file milestone** — `orchestrator/config.py` with `load_config() -> OrchestratorConfig`, required `~/.orchestrator.json`, no hardcoded fallbacks, `SystemExit` on missing file/key. Spec: `.ai-factory/notes/12-config-file.md`. Fields: `max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`. Python dataclass field for `usage_threshold_5h` is `usage_threshold_5h` (valid identifier). CLAUDE.md needs config creation step.
- **REPL milestone** — bare `uv run orchestrator` opens interactive session; commands: `implement <path>`, `test <path>`, `set <key> <value>`, `show`, `save`, `help`, `exit`; loads config from file, allows in-session overrides, `save` persists to `~/.orchestrator.json`. No roadmap task written yet — user confirmed they want it, needs task + spec.

**Uncommitted working-tree state:**
- `.ai-factory/ROADMAP.md` — modified (new tasks added)
- `.ai-factory/notes/12-config-file.md` — new file
- `.ai-factory/handoffs/01-orchestrator-config-repl-roadmap.md` — this file
- `docs/configuration.md` — rewritten
- `docs/how-it-works.md` — updated
- `docs/target-project.md` — updated

## 4. Next step
Add the REPL milestone to ROADMAP.md with a spec note (`.ai-factory/notes/13-repl.md`), then commit everything uncommitted in the orchestrator repo.

## 5. Working discipline
- Never commit without explicit user permission ("закомить")
- Show plan before making changes to existing files; direct edits for new files are fine
- Memory writes only on explicit triggers: "запомни", "remember this", "save to memory"
- Tasks added to roadmap get a spec note; spec note written first, then contract line in ROADMAP
- 3D mode for docs: write target state as if already shipped

## 6. Error log
- `endswith("REVIEW_PASS")` was the signal detection method — it both missed valid passes (stray `</content>` after the signal) and accepted false positives (`"no REVIEW_PASS"` at end of file). Fixed with `_has_signal()` scanning last 5 lines for exact match.
- Config field naming: originally proposed `5h_usage_threshold` / `weekly_usage_threshold` — user corrected to `usage_threshold_5h` / `usage_threshold_weekly` (suffix pattern, not prefix). Then `weekly_usage_threshold` → `usage_threshold_weekly`. Final names: `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`, `max_iterations`.
- ROADMAP edit failures: `## Completed` section header not found (was `## Next`); `- [ ]` grep returned nothing (tasks were already `[x]`). Always grep for exact text before editing.

## 7. Orientation
- **`ORCHESTRATOR_USAGE_THRESHOLD`** (old env var) → **`usage_threshold_5h`** (new config field). Don't confuse with `usage_threshold_weekly`.
- **Phase session** vs **milestone session**: milestone session is persisted to sidecar JSON (`.ai-factory/plans/{slug}.json`, key `planner`); phase session is in-memory only, lost on process restart.
- **`_has_signal`** is in `agents.py`, not `main.py`. It's a module-level function, not a method.
- **`docs/configuration.md`** is already in target (3D) state — it describes the config file as if implemented. The actual implementation is still pending.

## 8. Domain model spine
- **Config file is required, no fallbacks** — `~/.orchestrator.json` must exist with all four keys; missing → `SystemExit`. Don't add defaults. (`.ai-factory/notes/12-config-file.md`)
- **Phase boundary = any `##` or `###` heading** in ROADMAP.md — works across all project formats without modification. (`docs/target-project.md`, `docs/how-it-works.md`)
- **Signal detection = last-5-lines exact match** — `_has_signal(text, signal)` in `agents.py`; whole line must equal signal after strip. (`orchestrator/agents.py:25`)
- **Usage check = before every milestone, both thresholds** — not adaptive, not periodic; `_check_usage_limits()` in `main.py` called at top of both inline loops. (`orchestrator/main.py`)

## 9. Hard rules
- No `[x]` tasks are touched — only append new `[ ]` tasks to ROADMAP
- Spec note written before contract line in ROADMAP
- Config field names: `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`, `max_iterations` — these are final, don't rename
- `ORCHESTRATOR_CONFIG` is the only env var that remains (meta: path to config file)
- Docs language: Russian (artifacts); all doc files match existing language
