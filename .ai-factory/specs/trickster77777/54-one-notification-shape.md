# One notification, composed in one place

**Date:** 2026-08-09
**Source:** conversation context (`docs/concepts/fault-handling.md` § "Reporting a fault," the three paragraphs added ahead of this task: a notification is a signal not the account, its colour says whose problem it is, one shape composed in one place)

## Problem today

Nine call sites, each building its own alert text inline — no shared composer exists:

| Site | Alert type | Shape it builds |
|---|---|---|
| `main.py:244` | `task` | `f"{project}: Task done: {title}"` |
| `main.py:363` | `task` | `f"{project}: Task done: {title}"` |
| `main.py:398` | `done` | `f"All tasks done: {project}\n{summary}"` |
| `main.py:423` | `stop` | `f"Orchestrator stopped (manual): {project}\n{summary}"` |
| `main.py:509` | `task-fail` | `f"Orchestrator stopped: {project}\n{msg}\n{summary}"` |
| `main.py:516` | `stop` | `f"Orchestrator halted: {project}\n{msg}\n{summary}"` |
| `main.py:523` | `escalation` | `f"Orchestrator escalated: {project}\n{msg}\n{summary}"` |
| `main.py:526-530` | `stop` | `f"Orchestrator error: {project}\n{type}: {msg}\n{summary}"` |
| `runtime.py:20` | `stop` | `f"Orchestrator force-quit: {project}\n{summary}"` |

Three concrete defects, not one:

1. **The two task-done sites (`:244`, `:363`) invert the order and drop the run summary.** Every other alert leads with a verb and ends with `_run_summary()`; these two lead with the project name and never call it at all.
2. **`"stopped"` names two different outcomes.** `main.py:509` (`PipelineStopError` — a task exhausted its review budget without converging, alert type `task-fail`, red) and `main.py:423` (an operator's manual stop, alert type `stop`, yellow) both render the word "stopped." A person skimming a channel of these cannot tell a judgment about the work from an operator's own action without opening the message.
3. **The detail is cut by line, not by length.** `msg = str(e).splitlines()[0]` (`main.py:508`, `:515`, `:522`) takes the first line, however long it is. For `PipelineStopError`/`HaltError` that line is normally short. For `EscalationError`, `str(e)` is `f"{artifact_path}: {excerpt}"` (`agents.py`), where `excerpt` is a full line of model prose pulled from the `## Escalation` section (`agents.py:52-67`, `_escalation_excerpt`) — often a whole sentence or more. A one-line bound does nothing to it, so the alert delivers a paragraph of the sidecar's own record instead of a pointer to it.

## The change

**1. `Outcome`, one value per distinct outcome the orchestrator can report**, declared in `notify.py`:

```python
class Outcome(Enum):
    TASK_DONE = "task_done"        # a single task completed
    RUN_DONE = "run_done"          # every task in the roadmap done
    MANUAL_STOP = "manual_stop"    # operator soft-stop
    UNCONVERGED = "unconverged"    # PipelineStopError
    HALTED = "halted"              # HaltError
    ESCALATED = "escalated"        # EscalationError
    ERRORED = "errored"            # unrecognized Exception
    FORCE_QUIT = "force_quit"      # second Ctrl+C
```

Eight values for nine sites: `main.py:244` and `:363` are the same outcome reached by two code paths, not two outcomes, and share `TASK_DONE`.

**2. One word per outcome, no word shared:**

| Outcome | Word | Existing alert type (unchanged) |
|---|---|---|
| `TASK_DONE` | Completed | `task` |
| `RUN_DONE` | Finished | `done` |
| `MANUAL_STOP` | Stopped | `stop` |
| `UNCONVERGED` | Unconverged | `task-fail` |
| `HALTED` | Halted | `stop` |
| `ESCALATED` | Escalated | `escalation` |
| `ERRORED` | Errored | `stop` |
| `FORCE_QUIT` | Force-quit | `stop` |

`UNCONVERGED` and `MANUAL_STOP` no longer share a word — that is the second defect closed. Four outcomes still share the `stop` alert type (colour), and that is correct: colour answers "whose problem is it" (`fault-handling.md`'s new paragraph), and a halt, a manual stop, a force-quit, and an unrecognized error are all a problem in the machine or the operator, never a judgment about the work. The word is what tells them apart within that colour.

**3. The composer**, `notify.py`, beside `notify()`:

```python
_WORDS: dict[Outcome, str] = {
    Outcome.TASK_DONE: "Completed",
    Outcome.RUN_DONE: "Finished",
    Outcome.MANUAL_STOP: "Stopped",
    Outcome.UNCONVERGED: "Unconverged",
    Outcome.HALTED: "Halted",
    Outcome.ESCALATED: "Escalated",
    Outcome.ERRORED: "Errored",
    Outcome.FORCE_QUIT: "Force-quit",
}


def compose(outcome: Outcome, project: str, detail: str | None, run_summary: str) -> str:
    """The one place every notification's text is built."""
    lines = [f"{_WORDS[outcome]}: {project}"]
    if detail:
        lines.append(detail)
    lines.append(run_summary)
    return "\n".join(lines)
```

Envelope, pinned: the outcome's word, then the project, then the detail when there is one, then the run summary — always, including `TASK_DONE`/`RUN_DONE`, neither of which carries a run summary today.

**4. What each outcome's detail is:**

- `TASK_DONE` — the task's title, as the roadmap wrote it.
- `RUN_DONE`, `MANUAL_STOP`, `FORCE_QUIT`, `ESCALATED` — no detail; the alert is the word, the project, and the run summary.
- `UNCONVERGED`, `HALTED` — the first line of the exception's message, `str(e).splitlines()[0]`, exactly as today. The line cut stays: these messages open with a fixed summary clause and continue into a path or raw output, and the cut is what keeps the label and drops the rest.
- `ERRORED` — `f"{type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}"`, exactly as today. The class name and the interpreter's own message are not agent prose, and without them an unrecognized fault reports nothing at all.

**5. `report()`, the one entry every call site uses in place of `notify()`:**

```python
_ALERT_TYPES: dict[Outcome, str] = {
    Outcome.TASK_DONE: "task",
    Outcome.RUN_DONE: "done",
    Outcome.MANUAL_STOP: "stop",
    Outcome.UNCONVERGED: "task-fail",
    Outcome.HALTED: "stop",
    Outcome.ESCALATED: "escalation",
    Outcome.ERRORED: "stop",
    Outcome.FORCE_QUIT: "stop",
}


def report(config: "OrchestratorConfig", outcome: Outcome, project: str,
           detail: str | None, run_summary: str) -> None:
    """The one entry a call site uses: it composes the text and selects the alert type."""
    notify(config, compose(outcome, project, detail, run_summary), _ALERT_TYPES[outcome])
```

No call site names an alert type at all, so an inconsistent pairing of word and colour has nowhere to come from. `run_summary` is a parameter rather than something `notify.py` fetches, because `_run_summary()` lives in `runtime.py`, which already imports `notify` — reaching back would close a cycle.

`notify()` itself is unchanged, down to the line: its early returns, its emoji selection, and the five token strings all stay. `_ALERT_TYPES` reproduces exactly the tokens the sites pass today, so a `telegram_alerts` list written before this task selects exactly the alerts it always did. The existing table of outcome, word and token (§2, above) stays where it is — it is what a person reads; `_WORDS` and `_ALERT_TYPES` are what the code reads.

`main.py`'s nine call sites (eight calls, since `:244` and `:363` are one outcome) and `runtime.py`'s force-quit call `report(...)`, passing no token, and format no string of their own.

## Guards

- `notify()`'s alert-type gate (`config.telegram_alerts` membership check), its emoji selection (`_FAIL_ALERTS`/`_HALT_ALERTS`/`_ESCALATION_ALERTS`), and the five token strings (`task`, `done`, `stop`, `task-fail`, `escalation`) are untouched — `_ALERT_TYPES` reproduces exactly the token each outcome carries today, so a `telegram_alerts` list written before this task keeps selecting the same alerts it always did.
- `send_telegram` is not touched.
- `agents.py` is not touched by this task at all — no `path` field on `EscalationError`, no raise-site edit. The sidecar's `escalation` record (`_write_session(plan_path, "escalation", ...)`) keeps its exact current content regardless — a documented cross-repo contract (`CLAUDE.md`: sidecar fields are mirrored in the sibling skills repository's own artifact-protocol description) this task does not touch.
- Do not touch the escalation prompt or any agent prompt — the alert's shape is not the agent's business.

## Tests

`tests/test_notify.py`, beside the existing `sent`-fixture cases (`:22-107`):

- `compose()`'s envelope order: word, then project, then detail (when present), then run summary — asserted for one outcome with a detail and one without.
- The run summary appears on `TASK_DONE`'s composed text, which carries none today.
- Every `Outcome` member maps to a distinct word in `_WORDS` — a single assertion over the mapping's values, not a case per outcome.
- `_ALERT_TYPES` covers every `Outcome` member, each mapped to the token that outcome's site passes today — the guarantee that an existing configuration keeps working.
- `report()` passes `_ALERT_TYPES[outcome]` to `notify()` for every outcome, so the word and the colour cannot come apart.

`tests/test_runtime.py` and `tests/test_main.py` also change — they patch `notify` directly (`tests/test_runtime.py:185,214,237`, `tests/test_main.py:907`), so this task breaks them by construction, not by choice. Once a call site reports an outcome instead of calling `notify()`, no test name, docstring, or section comment in either file may go on naming a call the module can no longer make — the rule applies to every such identifier, not only the ones a reviewer happens to notice. A section comment this task rewrites loses its plan coordinate in the same edit; the ones it does not rewrite keep theirs.

## Verify

- `uv run pytest` green, including the cases above.
- `grep -n "notify(" orchestrator/main.py orchestrator/runtime.py` returns nothing — no site outside `notify.py` calls `notify(` at all. `grep -n "report(" orchestrator/main.py orchestrator/runtime.py` shows every call site.
- Manual trace: a task-fail alert and a manual-stop alert, side by side, read "Unconverged" and "Stopped" — no shared word; an escalation alert carries no detail line at all — word, project, and run summary only.

## What NOT to do

- Do not change any `telegram_alerts` token or the emoji each maps to.
- `send_telegram` is not touched — this task changes the text handed to `notify()`, never how a send is attempted.
- Do not touch `agents.py` at all — not `_escalation_excerpt`, not any `_write_session` call, not the sidecar's `escalation` record, not `EscalationError`'s declaration, not the escalation prompt. This task's fix is entirely in `notify.py` and its callers.
- Do not add any detail to the `ESCALATED` alert — not the role, not the excerpt, not the path. The alert is the word, the project, and the run summary, exactly like `RUN_DONE`, `MANUAL_STOP`, and `FORCE_QUIT`.
- Touch `notify.py`, `main.py` (the nine call sites plus the one resumed-escalation raise at `:237`), `runtime.py` (the one call site), `tests/test_notify.py`, `tests/test_runtime.py`, and `tests/test_main.py` only — never `agents.py`.
