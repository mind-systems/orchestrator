# Plan: 21.3 — One notification, composed in one place

## Context

Every notification is built inline at the site that raises it — eight `notify()` calls in `main.py`, one in `runtime.py` — so the envelope drifts by site: the two task-done sites lead with the project and omit the run summary, `"stopped"` names both an unconverged task and an operator stop, and the `ESCALATED` detail carries `f"{artifact_path}: {excerpt}"`, a filesystem path plus a line of model prose, past a first-line cut that bounds nothing when the whole message is one line. This task moves composition into `notify.py`: an `Outcome` enum, one word per outcome, and a single `report()` entry that selects the alert type, so no call site names a token or formats a string of its own.

**The detail is closed by removal, not by a cap.** Per the spec's § 4, `ESCALATED` carries no detail at all — the alert is the word, the project, and the run summary, exactly like `RUN_DONE`, `MANUAL_STOP`, and `FORCE_QUIT`. `UNCONVERGED`, `HALTED`, and `ERRORED` keep `str(e).splitlines()[0]` **exactly as today**, the `if str(e) else ''` guard included. There is no length cap and no `_cap()` helper: the escalation alert was the only one carrying a path or agent prose, and dropping its detail is what closes the defect.

**`agents.py` is untouched.** The spec's § Guards and § "What NOT to do" put the whole file out of scope — no `path` field on `EscalationError`, no raise-site edit, no `_escalation_excerpt` or `_write_session` change. The sidecar's `escalation` record keeps its exact content (a cross-repo contract, per `CLAUDE.md`). The resumed-escalation raise at `main.py:237` therefore needs no edit either: `EscalationError` stays single-argument, and the `ESCALATED` site reads nothing off the exception.

**All three test files are in scope by the spec's own hand** (§ Tests `:138`, § "What NOT to do" `:152`): `tests/test_runtime.py` and `tests/test_main.py` patch `notify` directly, so this task breaks them by construction. The spec attaches a standing rule to that — once a site reports an outcome, *no* test name, docstring, or section comment in either file may go on naming a call the module can no longer make, "the rule applies to every such identifier, not only the ones a reviewer happens to notice." Tasks 6 applies it exhaustively rather than case by case.

**Plan coordinates in test section comments.** Phase 19's opening paragraph (`roadmaps/trickster77777.md:89`, below the header at `:87`) states the rule: "A later task that rewrites one of those lines for its own reasons takes the coordinate with it; a line no task touches keeps its prefix until the cross-repo ask is answered." Twenty-one `# Task N:` prefixes sit in the three files this task edits (`test_main.py` 14, `test_runtime.py` 5, `test_notify.py` 2). Exactly one of those lines is rewritten here — `test_runtime.py:173-174`, whose trailing clause names `notify` — so exactly one loses its coordinate. The other twenty are untouched lines and keep their prefixes; this task performs no sweep, which 19.1 forbids.

## Settings
- Testing: yes — `tests/test_notify.py`, `tests/test_runtime.py`, `tests/test_main.py`, all three named by the spec
- Logging: minimal
- Docs: no — `docs/concepts/fault-handling.md` § "Reporting a fault" already states this behaviour in the present tense ahead of the code, and no doc quotes a per-site message string

## Tasks

### Phase 1: The composer

- [x] **Task 1: `Outcome` in `notify.py`**
  Files: `orchestrator/notify.py`
  Add `from enum import Enum` to the imports and declare, below the `_FAIL_ALERTS`/`_HALT_ALERTS`/`_ESCALATION_ALERTS` constants and above `notify()`, `class Outcome(Enum)` with exactly the eight members and values the spec pins: `TASK_DONE = "task_done"`, `RUN_DONE = "run_done"`, `MANUAL_STOP = "manual_stop"`, `UNCONVERGED = "unconverged"`, `HALTED = "halted"`, `ESCALATED = "escalated"`, `ERRORED = "errored"`, `FORCE_QUIT = "force_quit"`, each with the short trailing comment naming the site or exception it stands for. `enum` is stdlib, so the module docstring's "stdlib only, no new dependencies" stays true. Do not touch `notify()`, `send_telegram`, the three alert-set constants, or any token string.

- [x] **Task 2: `_WORDS` and `compose()`** (depends on Task 1)
  Files: `orchestrator/notify.py`
  Beside `notify()`, add `_WORDS: dict[Outcome, str]` mapping every member to its word — `Completed`, `Finished`, `Stopped`, `Unconverged`, `Halted`, `Escalated`, `Errored`, `Force-quit` — one word per outcome, none shared. Add `def compose(outcome: Outcome, project: str, detail: str | None, run_summary: str) -> str` building the pinned envelope: `f"{_WORDS[outcome]}: {project}"`, then `detail` when it is truthy, then `run_summary` — always, including `TASK_DONE`/`RUN_DONE`, neither of which carries one today — joined with `"\n"`. The detail is appended as given: no cap, no truncation, no ellipsis. The module already carries `from __future__ import annotations`, so the `str | None` annotation holds.

- [x] **Task 3: `_ALERT_TYPES` and `report()`** (depends on Task 2)
  Files: `orchestrator/notify.py`
  Add `_ALERT_TYPES: dict[Outcome, str]` reproducing exactly the token each site passes today: `TASK_DONE→"task"`, `RUN_DONE→"done"`, `MANUAL_STOP→"stop"`, `UNCONVERGED→"task-fail"`, `HALTED→"stop"`, `ESCALATED→"escalation"`, `ERRORED→"stop"`, `FORCE_QUIT→"stop"`. Add `def report(config: "OrchestratorConfig", outcome: Outcome, project: str, detail: str | None, run_summary: str) -> None` whose whole body is `notify(config, compose(outcome, project, detail, run_summary), _ALERT_TYPES[outcome])` — calling the module-global `notify`, which is what keeps `notify_module.notify` patchable for Task 7's last case. `run_summary` stays a parameter: `_run_summary()` lives in `runtime.py`, which already imports `notify` (`ARCHITECTURE.md:48` pins that direction), so fetching it here would close a cycle. `notify()` itself stays byte-identical — its gate, its emoji selection, and the five token strings all stay.

### Phase 2: Every call site reports an outcome

- [x] **Task 4: `main.py`'s eight call sites** (depends on Task 3)
  Files: `orchestrator/main.py`
  Replace `from .notify import notify` (`:16`) with `from .notify import Outcome, report`, and rewrite each site to name an outcome and a detail, never a token. `config`, `project_dir`, and `_run_summary` (imported at `:19`) are already in scope at every one:
  - `:244` and `:363` (task done, two code paths, one outcome) → `report(config, Outcome.TASK_DONE, project_dir.name, task.title, _run_summary())`.
  - `:398` (all tasks done) → `report(config, Outcome.RUN_DONE, project_dir.name, None, _run_summary())`.
  - `:423` (manual stop) → `report(config, Outcome.MANUAL_STOP, project_dir.name, None, _run_summary())`.
  - `:508-509` (`PipelineStopError`) → keep `msg = str(e).splitlines()[0]` exactly as it stands, then `report(config, Outcome.UNCONVERGED, project_dir.name, msg, _run_summary())`.
  - `:515-516` (`HaltError`) → keep its `msg = ...` line unchanged, then `report(config, Outcome.HALTED, project_dir.name, msg, _run_summary())`.
  - `:522-523` (`EscalationError`) → **delete** the `msg = str(e).splitlines()[0]` line at `:522` and call `report(config, Outcome.ESCALATED, project_dir.name, None, _run_summary())`. Deleting `msg` here is safe: it has no second use, since the `print` at `:520` reads `e`, not `msg`. No path, no excerpt, no role — this is the defect the task exists to close.
  - `:526-530` (unrecognized `Exception`) → `report(config, Outcome.ERRORED, project_dir.name, f"{type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}", _run_summary())` — the detail expression character-for-character as today, the `if str(e) else ''` guard included. The bare `raise` after it stays.
  The `print` blocks in each `except` arm, the `sys.exit(0)` calls, and the resumed-escalation raise at `:237` are unchanged — `agents.py` is out of scope, so `EscalationError` stays single-argument and that raise needs no edit.

- [x] **Task 5: `runtime.py`'s force-quit site** (depends on Task 4)
  Files: `orchestrator/runtime.py`
  Replace `from .notify import notify` (`:11`) with `from .notify import Outcome, report`, and rewrite `:20` to `report(state.config, Outcome.FORCE_QUIT, state.project_dir.name, None, _run_summary())`. The enclosing `if state.config is not None and state.project_dir is not None:` guard, the `kill_active_child()` call, and `sys.exit(1)` are unchanged.

### Phase 3: Tests

- [x] **Task 6: repoint `test_runtime.py` and `test_main.py`** (depends on Task 5)
  Files: `tests/test_runtime.py`, `tests/test_main.py`
  Both files patch `notify` directly and break by construction. Apply the spec's standing rule (§ Tests `:138`) to **every** identifier in both files, not only the ones listed here: after this task neither module can call `notify`, so no name, docstring, or section comment may go on saying it.

  `tests/test_runtime.py` — repoint the three `_handle_sigint` tests: `monkeypatch.setattr(runtime, "notify", notify_mock)` at `:185`, `:214`, `:237` becomes `"report"`, and add `from orchestrator.notify import Outcome` to the imports. In the positive test the recorded positional args are now `(config, Outcome.FORCE_QUIT, "myproject", None, <summary>)`: assert `call_args[0][0] is state.config`, `call_args[0][1] is Outcome.FORCE_QUIT`, and `call_args[0][2] == "myproject"` — the outcome replaces the old substring check for `"force-quit"` and the `"stop"` token, which no site names any more. The two negative tests keep `assert_not_called()`. Rename accordingly, all three tests and not two — the standing rule has no survivor, and one behaviour must not be described with two verbs across three adjacent tests: local `notify_mock` → `report_mock` in all three; the name at `:178` (`test_handle_sigint_second_press_notifies_when_config_and_project_dir_set`) → `test_handle_sigint_second_press_reports_when_config_and_project_dir_set`, alongside the names at `:207` and `:230` (`..._no_notify_when_config_none`, `..._no_notify_when_project_dir_none`) → `..._no_report_when_...`; the docstring at `:179` ("send a force-quit notify" → "…report") and the two "WITHOUT notifying" → "WITHOUT reporting". The section comment at `:173-174` is rewritten here ("with and without the notify guard" → "the report guard") and therefore **loses its `# Task 5:` prefix in the same edit**, per Phase 19's rule quoted in § Context — it is the one line in the three files that this task rewrites.

  `tests/test_main.py` — `_run_cli_with` (`:893-909`) patches `main_module.notify` with a 3-arg fake; patch `"report"` instead, with `def _fake_report(config, outcome, project, detail, run_summary)` recording `(outcome, detail)`, and update its docstring (`:894`) to name `report`. Add `from orchestrator.notify import Outcome` to the import block (`:10-22` imports `orchestrator.agents`, `.config`, `.main`, `.usage` today, never `.notify`); `EscalationError` is already imported at `:13`. Then, for the three existing routing tests at `:912-933`:
  - assert `recorded[-1][0]` is `Outcome.UNCONVERGED`, `Outcome.HALTED`, `Outcome.ERRORED` respectively — `RateLimitError` (`:922`) is a `HaltError` subclass, so it routes to `HALTED`;
  - **rename all three** to what they now assert — `test_cli_pipeline_stop_error_routes_to_unconverged`, `test_cli_rate_limit_error_routes_to_halted`, `test_cli_generic_exception_routes_to_errored_and_reraises`. The old names name alert tokens (`..._to_task_fail`, `..._to_stop` twice) that no `main.py` site names any more, and the two `_routes_to_stop` names would otherwise have one word serving two different outcomes — the phase's own defect #2, reproduced in the test layer by the task that removes it from the alert layer. Token routing is asserted in Task 7, on `_ALERT_TYPES` directly;
  - rewrite the three docstrings (`:913`, `:921`, `:929`) to match: "Should record `Outcome.UNCONVERGED`…", "…`Outcome.HALTED`…", "…`Outcome.ERRORED` and re-raise a generic Exception."
  - add a fourth routing case, `test_cli_escalation_error_routes_to_escalated_with_no_detail`, running `_run_cli_with(monkeypatch, EscalationError("some/plan.md: a paragraph of model prose"))` and asserting `recorded[-1] == (Outcome.ESCALATED, None)`. This is what spends the `detail` the fake records, and it is the only test that pins the defect the task exists to close: a future edit restoring `msg = str(e).splitlines()[0]` at that site would otherwise put the path and the excerpt back into the alert silently, with a green suite.

  The section comment above those tests (`:880-881`, `# cli() exception-routing tests`) carries no coordinate and already labels by behaviour — leave it. Add nothing else; the composer's own cases belong to Task 7.

- [x] **Task 7: `tests/test_notify.py` — the composer's cases** (depends on Task 6)
  Files: `tests/test_notify.py`
  Add the spec's five cases below the existing `sent`-fixture cases (`:22-107`), which stay untouched — including their two `# Task N:` headers at `:35` and `:85`, which this task does not rewrite and which therefore keep their prefixes. Widen the module docstring (`:1`, today `"""Unit tests for notify() — emoji-prefix mapping and telegram gating."""`) to cover the composer alongside `notify()`'s gating, and label the new sections by the behaviour under test. Import `Outcome`, `compose`, `report`, `_WORDS`, `_ALERT_TYPES` from `orchestrator.notify`; `notify_module` is already imported at `:5`:
  - `compose()`'s envelope order — word, then project, then detail, then run summary — asserted for one outcome carrying a detail; and for one carrying `None`, that the text is exactly two lines (word-and-project, then the run summary).
  - `TASK_DONE`'s composed text carries the run summary, which it does not today.
  - Every `Outcome` member maps to a distinct word — one assertion over `_WORDS` (`set(_WORDS) == set(Outcome)` and `len(set(_WORDS.values())) == len(Outcome)`), not a case per outcome.
  - `_ALERT_TYPES` covers every `Outcome` member, each mapped to the token that outcome's site passes today — the eight pinned pairs, the guarantee that a `telegram_alerts` list written before this task keeps selecting the same alerts.
  - `report()` passes `_ALERT_TYPES[outcome]` to `notify()` for every outcome — monkeypatch `notify_module.notify` with a recorder, loop over `Outcome`, assert the token, so the word and the colour cannot come apart.

- [x] **Task 8: verify** (depends on Task 7)
  Files: none
  `uv run pytest` — green. `grep -n "notify(" orchestrator/main.py orchestrator/runtime.py` — zero hits (the new import line carries no parenthesis). `grep -n "report(" orchestrator/main.py orchestrator/runtime.py` — exactly nine hits, eight in `main.py` and one in `runtime.py`. Read-level check of the manual trace the spec names: a task-fail alert and a manual-stop alert read "Unconverged" and "Stopped", sharing no word; and an escalation alert carries no detail line at all — word, project, and run summary only.
