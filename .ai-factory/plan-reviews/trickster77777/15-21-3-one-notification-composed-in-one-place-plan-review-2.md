# Plan Review: 21.3 — One notification, composed in one place (round 2)

## Code Review Summary

**Files Reviewed:** plan + 6 target files (`orchestrator/notify.py`, `orchestrator/main.py`, `orchestrator/runtime.py`, `tests/test_notify.py`, `tests/test_runtime.py`, `tests/test_main.py`) + spec `54-one-notification-shape.md` + contract line `roadmaps/trickster77777.md:115` + governing spec `docs/concepts/fault-handling.md`
**Risk Level:** 🟡 Medium — no correctness, security, or API defect; one finding, in Task 6's test-layer naming, and it is the residue of round 1's finding #1 in the file that round 1 believed already handled.

### Context Gates

- **Architecture (`.ai-factory/ARCHITECTURE.md`) — OK.** The dependency rules confirm the plan's reasoning: `runtime`→`notify` already exists in the ✅ list of downward support imports, so `notify` fetching `_run_summary()` from `runtime` would close a cycle. Keeping `run_summary` a parameter of `report()` (Task 3) is the only shape that holds the direction. `notify.py`'s module comment ("Support: Telegram alerts") stays accurate with a composer added.
- **Rules — WARN (file absent).** No `.ai-factory/RULES.md` in this repo; no explicit convention file to check against.
- **Roadmap — OK.** `roadmaps/trickster77777.md:115` is the task; its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/54-one-notification-shape.md`, whose governing spec is `docs/concepts/fault-handling.md`. The plan implements that tree: `:72` (a signal, not the account), `:74`/`:83` (colour says work vs. machine — preserved by `_ALERT_TYPES` reproducing today's tokens verbatim), `:85` ("one shape, composed in one place"), rules 5 and 6 at `:93-94`. `Docs: no` is correct — the concept page is already written in the present tense ahead of the code, and no doc quotes a per-site message string (`docs/reference/configuration.md:77-87` pins tokens and colours only, both untouched; `docs/features/escalation.md:25` and `docs/concepts/outcomes.md:16` link to that table rather than copying text).
- **Plan-layer citation rule (Phase 19) — OK.** § Context now labels `roadmaps/trickster77777.md:89` as the phase's opening paragraph, below the header at `:87` — verified, and the quoted sentence is verbatim. The prefix census is verifiable: `test_main.py` 14, `test_runtime.py` 5, `test_notify.py` 2 = 21, counted and matching; only `test_runtime.py:173-174` is rewritten by this task and only it loses its coordinate; the section comment above the `cli()` routing tests (`:879-881`) carries no coordinate and already labels by behaviour, as the plan says.

### Round-1 findings — all three closed

- **#1 (routing test names)** — closed. Task 6 now renames all three to `..._routes_to_unconverged` / `..._routes_to_halted` / `..._routes_to_errored`, states why (`_routes_to_stop` twice would reproduce defect #2 in the test layer), and points token routing at Task 7's `_ALERT_TYPES` assertion.
- **#2 (`detail` recorded but never read)** — closed, and closed the sharp way: the fourth routing case `test_cli_escalation_error_routes_to_escalated_with_no_detail` asserts `recorded[-1] == (Outcome.ESCALATED, None)`, which is the only test in the plan that pins the defect the task exists to close. Verified reachable: `EscalationError` is a direct `Exception` subclass (`agents.py:168`), not a `HaltError` subclass, so `cli()`'s `except EscalationError` arm (`:518`) is the one that fires.
- **#3 (`:89` labelled as the header)** — closed; the plan now names the header at `:87` and the paragraph at `:89` separately.

### Verified against the codebase (no defect found)

- `main.py:16` import, `:19` `_run_summary` import, and the eight `notify()` sites at `:244`, `:363`, `:398`, `:423`, `:509`, `:516`, `:523`, `:526-530` — all confirmed at those exact lines, with `msg = str(e).splitlines()[0]` at `:508`, `:515`, `:522`. `config` and `project_dir` are in scope at all eight (`process_task(...)` params at `:198`, `_run_dynamic_loop(...)` params at `:370`, `cli()`'s locals at `:495`/`:497`).
- Dropping `msg` in the `EscalationError` arm (Task 4) is safe: `print(f"ESCALATED — {e}")` (`:520`) reads `e`, not `msg`, and `msg` has no other use in that arm.
- The `ERRORED` detail expression the plan pins matches `:528` character-for-character, `if str(e) else ''` included.
- `runtime.py:11`/`:20` and the `state.config is not None and state.project_dir is not None` guard — confirmed; `_run_summary()` is defined natively at `:38`, so no new import.
- `notify.py` carries `from __future__ import annotations` (`:3`) and a `TYPE_CHECKING` import of `OrchestratorConfig` (`:10-11`), so `detail: str | None`, `config: "OrchestratorConfig"`, and the module-level `dict[Outcome, str]` annotations all hold. `enum` is stdlib — the docstring's "stdlib only, no new dependencies" stays true.
- Patch targets hold: `from .notify import Outcome, report` binds `report` into both namespaces, so `main_module.report` / `runtime.report` stay monkeypatchable; `report()` calling the module-global `notify` keeps `notify_module.notify` patchable for Task 7's last case.
- Test coordinates: `test_runtime.py:173-174` comment, `:178`/`:207`/`:230` names, `:185`/`:214`/`:237` patch lines; `test_main.py:893-909` `_run_cli_with` (its docstring at `:894`, its `main_module.notify` patch at `:907`) and its three consumers at `:912-933` — all confirmed. `_run_cli_with` has exactly those three consumers, so retyping the recorded tuple breaks nothing else; `EscalationError` is already imported at `:13`, and the import block never imports `.notify`.
- The positional-argument claim holds: with `Mock(name="project_dir")` plus `.name = "myproject"` (`:189-190`), `call_args[0][2] == "myproject"` after the rewrite.
- `RateLimitError` is a `HaltError` subclass (`agents.py:154`), so the `:922` case does route to `HALTED`.
- No other module calls `notify()` and no other test patches it — the eight `main.py` sites, the one in `runtime.py`, and `test_runtime.py`/`test_main.py` are the complete set. Task 8's greps will therefore behave as stated: zero `notify(` hits (the new import line carries no parenthesis), exactly nine `report(` hits, and no pre-existing `report(` in either module to inflate the count.

### Critical Issues

**1. (MEDIUM — Task 6) The positive `test_runtime.py` test keeps `notifies` in its name while its own docstring and both its siblings move to `report`.**
Task 6 enumerates, for `test_runtime.py`: the three patch lines, `notify_mock` → `report_mock` in all three, the names at `:207` and `:230` (`..._no_notify_when_...` → `..._no_report_when_...`), the docstring at `:179`, the two "WITHOUT notifying" → "WITHOUT reporting", and the section comment at `:173-174`. The name at `:178` — `test_handle_sigint_second_press_notifies_when_config_and_project_dir_set` — is not in the list.

After Task 5, `runtime.py` calls `report()` and can no longer call `notify()`. The spec's standing rule (`54-one-notification-shape.md:138`) admits no exemption: "no test name, docstring, or section comment in either file may go on naming a call the module can no longer make — the rule applies to every such identifier, not only the ones a reviewer happens to notice." Three consequences, all inside one file after one edit:

- The test's name says `notifies` while its own docstring (`:179`, rewritten by this task) says `report` — name and body disagreeing inside one test, which is exactly the shape round 1 flagged in `test_main.py` and this revision fixed there.
- Its two siblings become `..._no_report_when_config_none` / `..._no_report_when_project_dir_none`. One behaviour, described with two verbs, across three adjacent tests — and the verb that survives is the one naming the call that no longer exists.
- The plan's § Context claims Task 6 applies the rule "exhaustively rather than case by case", and Task 6 opens by extending it to "**every** identifier in both files, not only the ones listed here". But everywhere else the plan enumerates to the line, so a list that names `:207`, `:230`, `:179` and skips `:178` reads as a deliberate exemption, not as an omission the standing sentence sweeps up. Round 1 already recorded (its own § finding #1) the belief that `test_runtime.py` renames "all three tests, including the positive one" — that belief is not what the plan text says.

Fix inside Task 6's enumeration: rename `:178` alongside its siblings (e.g. `test_handle_sigint_second_press_reports_when_config_and_project_dir_set`), so the triple names one verb and the rule has no survivor.

### Positive Notes

- Task 6's fourth case is the plan's strongest addition: it is the only assertion anywhere that `main.py:522`'s site passes no detail, and the plan says exactly why it exists — a future edit restoring `msg = str(e).splitlines()[0]` there would otherwise put the path and the excerpt back with a green suite.
- The import-cycle reasoning for `run_summary` as a parameter (Task 3) is stated where an implementer would be tempted to "simplify" it away, and it matches `ARCHITECTURE.md`'s ✅ line for support-module direction.
- Task 4 pins the `ERRORED` detail character-for-character and Task 4/§ Context pin the `EscalationError` deletion with its safety argument (`print` reads `e`, not `msg`), so the two sites whose text is genuinely load-bearing cannot drift during a mechanical rewrite.
- § Context states plainly what is *not* being done and why — no `_cap()` helper, no `agents.py` edit, no `:237` edit, no coordinate sweep — which is what keeps a plan of eight small tasks from growing a ninth during implementation.
- Task 8 turns the spec's § Verify into two greps with expected hit counts plus one read-level check, so "no call site names a token" is falsifiable rather than asserted.

## Deferred observations

- Affects: `.ai-factory/specs/trickster77777/54-one-notification-shape.md` § 4 / `docs/concepts/fault-handling.md:72` (rule 5) — the spec keeps `str(e).splitlines()[0]` for `UNCONVERGED` and `HALTED` on the grounds that those messages "open with a fixed summary clause and continue into a path or raw output". Two live raise sites do not: `RateLimitError(result_text)` (`agents.py:350`) makes the whole exception message the agent's own result text, whose first line is a line an agent wrote, and `_resolve_roadmap_relpath`'s owner-mismatch `HaltError` (`main.py:152-155`) is a single line carrying a roadmap path and a quoted file line. Both are `HaltError`, so both reach the `HALTED` detail intact — the alert keeps carrying a path or agent prose, which is what `fault-handling.md`'s rule 5 forbids. Closing it means either bounding the detail by length in `compose()`/`report()` or reshaping those two raise sites, and both contradict this task's ratified pins (`agents.py` is explicitly out of the touch-list; § 4 pins the line cut "exactly as today"), so it belongs to a later task in Phase 21, not to this plan.
