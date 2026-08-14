# Plan Review: 21.3 — One notification, composed in one place

## Code Review Summary

**Files Reviewed:** plan + 6 target files (`orchestrator/notify.py`, `orchestrator/main.py`, `orchestrator/runtime.py`, `tests/test_notify.py`, `tests/test_runtime.py`, `tests/test_main.py`) + spec `54-one-notification-shape.md` + contract line `roadmaps/trickster77777.md:115`
**Risk Level:** 🟡 Medium — no correctness or security defect; three findings, all in Task 6's test-layer naming and coverage.

### Context Gates

- **Architecture (`.ai-factory/ARCHITECTURE.md`) — OK.** The dependency rules (`:46`, `:48`, `:61`) place `notify.py` as a leaf support module and permit `main`→`notify` and `runtime`→`notify`. `report()` taking `run_summary` as a parameter (Task 3) is exactly what keeps that direction one-way — `runtime`→`notify` already exists, so a `notify`→`runtime` fetch of `_run_summary()` would close a cycle and break `:48`. The plan states this and is right. The module comment at `:28` ("Support: Telegram alerts") stays accurate.
- **Rules — WARN (file absent).** No `.ai-factory/RULES.md` in this repo; no explicit convention file to check against.
- **Roadmap — OK.** `roadmaps/trickster77777.md:115` (Phase 21) is the task; its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/54-one-notification-shape.md`, whose governing spec is `docs/concepts/fault-handling.md` (Phase 21 header, `:109`). The plan implements that tree: `fault-handling.md:72` ("a signal, not the account", detail is a short fixed label or nothing), `:74`/`:83` (colour says work vs. machine — preserved by `_ALERT_TYPES` reproducing today's tokens), `:85` ("one shape, composed in one place"). The doc is already written in the present tense ahead of the code, so `Docs: no` is correct — no doc goes stale, and none pins the per-site message text (`docs/reference/configuration.md:79-85` pins tokens and colours only, both untouched).
- **Plan-layer citation rule (Phase 19) — OK.** The plan's § Context reading of the Phase 19 rule is correct and its coordinate handling is verifiable: 21 `# Task N:` prefixes across the three test files (`test_main.py` 14, `test_runtime.py` 5, `test_notify.py` 2 — counted, matches), only `test_runtime.py:173` is rewritten by this task, and only that one loses its prefix.

### Verified against the codebase (no defect found)

Every coordinate and API claim in the plan checks out against the files as they stand:

- `main.py:16` import, and the eight `notify()` sites at `:244`, `:363`, `:398`, `:423`, `:509`, `:516`, `:523`, `:526-530` — all confirmed, with the surrounding `msg = str(e).splitlines()[0]` lines at `:508`, `:515`, `:522` exactly where the plan says.
- Dropping `msg` in the `EscalationError` arm (Task 4) is safe: `msg` has no second use — `print(f"ESCALATED — {e}")` (`:520`) reads `e`, not `msg`.
- `_run_summary` is already imported into `main.py` (`:19`) and defined natively in `runtime.py` (`:38`), so no new import is needed at either call site.
- `runtime.py:11`/`:20` and the `state.config is not None and state.project_dir is not None` guard — confirmed.
- `notify.py` carries `from __future__ import annotations` and a `TYPE_CHECKING` import of `OrchestratorConfig`, so `report`'s `config: "OrchestratorConfig"` and `detail: str | None` annotations, and the module-level `dict[Outcome, str]` annotations, all hold. `enum` is stdlib — the module's "stdlib only, no new dependencies" docstring stays true.
- Patch targets: `report` bound into `main`'s and `runtime`'s namespaces by `from .notify import Outcome, report` remains monkeypatchable as `main_module.report` / `runtime.report`; `report()` calling the module-global `notify` keeps `notify_module.notify` patchable for Task 7's last case.
- Test coordinates: `test_runtime.py:173-174` section comment, `:178`/`:207`/`:230` test names, `:185`/`:214`/`:237` patch lines; `test_main.py:893-909` `_run_cli_with` and its three consumers at `:912-933` — all confirmed, and `_run_cli_with` has exactly those three consumers, so retyping the recorded tuple breaks nothing else.
- The positional-argument claim in Task 6 is right: `report(state.config, Outcome.FORCE_QUIT, state.project_dir.name, None, _run_summary())` gives `call_args[0][2] == "myproject"` for the existing `Mock(name=...)`/`.name = "myproject"` fixture.
- `RateLimitError` is a `HaltError` subclass, so the `:922` test does route to `HALTED` — the plan's parenthetical is correct.
- Task 8's greps will behave as stated: after the change neither `main.py` nor `runtime.py` contains the substring `notify(` (the import line has no parenthesis), and `report(` yields exactly nine hits.
- No other module calls `notify()` — the eight `main.py` sites and the one in `runtime.py` are the complete set.

### Critical Issues

**1. (MEDIUM — Task 6) The three `cli()` routing test names keep the alert token while their assertions and docstrings move to the outcome.**
The plan rewrites the three docstrings to "Should record `Outcome.UNCONVERGED`/`HALTED`/`ERRORED`" but freezes the names `test_cli_pipeline_stop_error_routes_to_task_fail`, `test_cli_rate_limit_error_routes_to_stop`, `test_cli_generic_exception_routes_to_stop_and_reraises`. Three problems follow from that in one edit:

- Name and docstring end up disagreeing inside the same test — the name claims a token, the body asserts an outcome, and after this task no site in `main.py` names a token at all. The spec (`:138`) states the rule without an exemption: "no test name, docstring, or section comment in either file may go on naming a call the module can no longer make — the rule applies to every such identifier, not only the ones a reviewer happens to notice."
- The plan applies that same rule maximally in `test_runtime.py` (renaming all three tests, including the positive one) and then exempts the three in `test_main.py`. One rule, two treatments, in one task.
- Two of the three names still share `_routes_to_stop` while now asserting two *different* outcomes (`HALTED`, `ERRORED`). That is the phase's own defect #2 — one word serving two outcomes — reproduced in the test layer by the very task that removes it from the alert layer.

The plan's rationale ("the routing they name is still true, carried by `_ALERT_TYPES`") is true as behaviour but not as description: after Task 6 these tests no longer assert token routing at all — Task 7 does, in another file. Rename to what each test asserts (`..._routes_to_unconverged`, `..._routes_to_halted`, `..._routes_to_errored`), and fold that into Task 6's standing-rule paragraph so the exemption does not survive into implementation.

**2. (LOW — Task 6) `_fake_report` is specified to record a `detail` no assertion ever reads.**
Task 6 pins the fake as recording `(outcome, detail)`, but every assertion it then specifies reads `recorded[-1][0]`. Nothing anywhere reads index 1, so the plan mandates dead data in a test helper. It also leaves the spec's defect #3 — the escalation alert carrying `f"{artifact_path}: {excerpt}"` — pinned by no test at all: `compose()`'s cases in Task 7 prove the envelope drops a falsy detail, but nothing proves that `main.py:522`'s site passes `None`, and a future edit re-adding `msg = str(e).splitlines()[0]` there would restore the paragraph-of-prose alert silently, with a green suite. Pick one and state it in the plan: either record the outcome alone, or keep the field and spend it — the cheapest spend inside the plan's existing three tests is asserting the detail the first-line cut produces (`recorded[-1][1] == "boom"` for `UNCONVERGED`/`HALTED`), and the sharpest is a fourth routing test on `EscalationError` asserting `recorded[-1] == (Outcome.ESCALATED, None)`.

**3. (MINOR — § Context) `roadmaps/trickster77777.md:89` is the phase's opening paragraph, not its header.**
The plan writes "the phase header (`:89`) states the rule directly". The header `### Phase 19 — Test files labelled by behavior, not by plan coordinate` is at `:87`; `:89` is the paragraph below it, which is indeed where the rule is stated ("A later task that rewrites one of those lines for its own reasons takes the coordinate with it; a line no task touches keeps its prefix until the cross-repo ask is answered"). The coordinate is right and the quotation is right — only the label is wrong. Call it the phase's opening paragraph.

### Positive Notes

- The import-cycle reasoning for `run_summary` as a parameter (Task 3) is stated where an implementer would otherwise be tempted to "simplify" it away, and it matches the real dependency direction in `ARCHITECTURE.md:48`.
- Task 4 pins the `ERRORED` detail expression character-for-character, including the `if str(e) else ''` guard, so the one site whose text is genuinely load-bearing cannot drift during the rewrite.
- The § Context paragraph on plan-coordinate handling does the hard part of the Phase 19 rule properly: it counts the prefixes, names the single line that is rewritten, and says why the remaining twenty stay — pre-empting exactly the sweep 19.1 forbids.
- Task 8 converts the spec's § Verify into two greps with expected hit counts plus one read-level check, so "no call site names a token" is falsifiable rather than asserted.
- Task 7 keeps the existing `sent`-fixture cases and their two coordinates untouched, and widens the module docstring instead — the minimal edit consistent with both the spec's § Tests and the Phase 19 rule.

## Deferred observations

- Affects: `.ai-factory/specs/trickster77777/54-one-notification-shape.md` § 4 / `docs/concepts/fault-handling.md:72` (rule 5) — the spec keeps `str(e).splitlines()[0]` for `UNCONVERGED` and `HALTED` on the grounds that those messages "open with a fixed summary clause and continue into a path or raw output". Two live raise sites do not: `RateLimitError(result_text)` (`agents.py:350`) makes the whole exception message the agent's own result text, whose first line is a line an agent wrote, and `_resolve_roadmap_relpath`'s owner-mismatch `HaltError` (`main.py:152-155`) is a single line carrying a roadmap path and a quoted file line. Both are `HaltError`, so both reach the `HALTED` detail intact — the alert keeps carrying a path or agent prose, which is what `fault-handling.md`'s rule 5 forbids. Closing it means either bounding the detail by length in `compose()`/`report()` or reshaping those two raise sites, and both contradict this task's ratified pins (`agents.py` is explicitly out of the touch-list; § 4 pins the line cut "exactly as today"), so it belongs to a later task in Phase 21, not to this plan.
