# What diverges now: the modules do not yet follow the layer map

**Date:** 2026-10-11
**Source:** the user's go in chat on 2026-10-11 («давай дип по 29»), under `.ai-factory/ARCHITECTURE.md`

Governing spec: [ARCHITECTURE.md](../../ARCHITECTURE.md) — § Dependency Rules, § Folder Structure, § What varies.

The architecture's layer map, the modules it names and the home it gives the port and the kind type are not yet the code's:

- **Modules import `agents` for things that belong lower.** `usage` imports it for `HaltError` alone. `resume` imports it for `_read_sessions` and `VerifyKind`, and for `REVIEW_VERIFY` and `TEST_RUN_VERIFY`, which only its `_detect_task_step` and `_detect_test_task_step` wrappers use; only tests call those wrappers. `runtime` imports it for `kill_active_child`, which `_run_claude` also calls.
- **`agents.py` holds several concerns together:** the outcome exceptions (`HaltError` and its subclasses, `PipelineStopError`, `EscalationError`); the sidecar helpers (`_read_sessions`, `_write_session`); signal and escalation recognition (`_has_signal`, `_has_escalation`, `_escalation_excerpt`); the CLI runner (`_resolve_claude`, `_run_claude`, result classification, retries, `kill_active_child`); `VerifierProtocol`, `VerifyKind` and its instances; and the roles.
- **`VerifyKind.make_verifier` is annotated with `PlannerReviewer`**, a role. Once the type sits in `ports.py`, vocabulary, that annotation reaches a layer above it.
- **`main.py` holds several concerns together:** the flow (`Mode` and its instances, `process_task`, `_run_dynamic_loop`, `_next_number`, `_artifact_dir`, `_git_commit`); the composition root and CLI (`_implement_loop`, `_test_loop`, `cli`); and named-roadmap resolution (`_USER_SLUG_SCRIPT`, `_git_config_value`, `_resolve_roadmap_relpath`, `_tests_sibling`, `_artifact_subdir`).
- **`usage` launches `claude /usage` itself by bare name**, not through the resolved CLI. The architecture reaches the CLI only through `claude_cli`.
- **The modules the architecture names do not exist:** `pipeline.py`, `layout.py`, `claude_cli.py`, `errors.py`, `protocol.py` and `ports.py`.
- **Docs name today's homes:** `CLAUDE.md` § Architecture puts `_run_claude` in `agents.py`.
