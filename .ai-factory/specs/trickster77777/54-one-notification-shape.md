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
3. **The detail is cut by line, not by length.** `msg = str(e).splitlines()[0]` (`main.py:508`, `:515`, `:522`) takes the first line, however long it is. For `PipelineStopError`/`HaltError` that line is normally short. For `EscalationError`, `str(e)` is `f"{artifact_path}: {excerpt}"` (`agents.py:398,445,494,547`), where `excerpt` is a full line of model prose pulled from the `## Escalation` section (`agents.py:52-67`, `_escalation_excerpt`) — often a whole sentence or more. A one-line bound does nothing to it, so the alert delivers a paragraph of the sidecar's own record instead of a pointer to it.

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

_DETAIL_CAP = 200


def _cap(detail: str) -> str:
    """Cut a detail to _DETAIL_CAP characters, marking the cut with an ellipsis."""
    return detail if len(detail) <= _DETAIL_CAP else detail[:_DETAIL_CAP] + "…"


def compose(outcome: Outcome, project: str, detail: str | None, run_summary: str) -> str:
    """The one place every notification's text is built."""
    lines = [f"{_WORDS[outcome]}: {project}"]
    if detail:
        lines.append(_cap(detail))
    lines.append(run_summary)
    return "\n".join(lines)
```

Envelope, pinned: the outcome's word, then the project, then the detail when there is one, then the run summary — always, including `TASK_DONE`/`RUN_DONE`, neither of which carries a run summary today.

**4. The detail cap.** 200 characters, cut on a character boundary with a trailing ellipsis, applied uniformly — a task's title, an exception's message, an escalation's artifact path all pass through the same cap. A bound on lines is what let a paragraph through; a bound on length cannot be defeated by removing the newlines.

**5. What each outcome's detail is:**

- `TASK_DONE` — the task's title.
- `RUN_DONE`, `MANUAL_STOP`, `FORCE_QUIT` — none; these carry no per-instance text today and gain none.
- `UNCONVERGED`, `HALTED` — the exception's message, `str(e)`, no longer cut at the first newline: the cap bounds it by length instead.
- `ERRORED` — the exception's class name, a colon, then its message: `f"{type(e).__name__}: {e}"`. The class name leads, so it survives the cap when the message is long and the tail does not; and an exception raised with no message still composes a detail that names what was raised, rather than an empty one that says nothing at all.
- `ESCALATED` — the artifact path only, never the excerpt, and never parsed out of a message string. `EscalationError` gains a field carrying that path:

  ```python
  class EscalationError(Exception):
      """Raised when an agent cannot honestly produce its mandated output because
      the missing decision is outside its authority — escalation, not halt."""
      def __init__(self, message: str, path: Path):
          super().__init__(message)
          self.path = path
  ```

  Each of `agents.py`'s four raise sites (`:398,445,494,547`) passes the path it already holds — `plan_path` for the planner and implementer, `review_path` for the two reviewers — as `path`; their message argument is untouched, whatever shape it already builds. `main.py:237`'s resumed-escalation re-raise passes `plan_path`, already in scope there — assigned earlier in the same function. The call site converts the path to a string where it builds the detail — `str(e.path)` — before calling `report()`; `compose()` receives only `str` or `None`, and `EscalationError.path` stays a `Path`. Both raise paths now hand the composer the same field, in the same way, so the two message shapes that exist today — a fresh escalation's and a resumed one's — stop mattering to it entirely.

**6. `report()`, the one entry every call site uses in place of `notify()`:**

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
- `agents.py` changes exactly two things: `EscalationError`'s declaration gains the `path` field, and each of its four `raise EscalationError(...)` call sites passes the path it already holds into that field. Nothing else in `agents.py` changes — `_escalation_excerpt`, the four `_write_session(plan_path, "escalation", ...)` calls, and the sidecar's `escalation` record they produce keep their exact current content. That record is a documented cross-repo contract (`CLAUDE.md`: sidecar fields are mirrored in the sibling skills repository's own artifact-protocol description) and this task does not touch it.
- The escalation detail carries the artifact's path only, never who raised it. The role (`planner`/`reviewer`/`plan-reviewer`/`implementer`) stays exactly where it already lives — the sidecar's `escalation` record — and is not surfaced in the alert; it is discoverable by opening the artifact itself, and recovering it into the alert too is not worth the `agents.py` surface it would take.
- Do not touch the escalation prompt or any agent prompt — the alert's shape is not the agent's business.

## Tests

`tests/test_notify.py`, beside the existing `sent`-fixture cases (`:22-107`):

- `compose()`'s envelope order: word, then project, then detail (when present), then run summary — asserted for one outcome with a detail and one without.
- The run summary appears on `TASK_DONE`'s composed text, which carries none today.
- A detail of 201 characters is cut to 200 plus a trailing ellipsis; one of exactly 200 is left whole.
- `ESCALATED`'s detail comes from `EscalationError.path`, never from parsing `str(e)` — constructed once with a fresh-style message and once with a resumed-style message, both carrying the same `path`, both produce the identical composed detail.
- Every `Outcome` member maps to a distinct word in `_WORDS` — a single assertion over the mapping's values, not a case per outcome.
- `_ALERT_TYPES` covers every `Outcome` member, each mapped to the token that outcome's site passes today — the guarantee that an existing configuration keeps working.
- `report()` passes `_ALERT_TYPES[outcome]` to `notify()` for every outcome, so the word and the colour cannot come apart.

## Verify

- `uv run pytest` green, including the cases above.
- `grep -n "notify(" orchestrator/main.py orchestrator/runtime.py` returns nothing — no site outside `notify.py` calls `notify(` at all. `grep -n "report(config" orchestrator/main.py orchestrator/runtime.py` shows every call site.
- Manual trace: a task-fail alert and a manual-stop alert, side by side, read "Unconverged" and "Stopped" — no shared word; an escalation alert shows the artifact's path in under 200 characters, not the excerpt.

## What NOT to do

- Do not change any `telegram_alerts` token or the emoji each maps to.
- `send_telegram` is not touched — this task changes the text handed to `notify()`, never how a send is attempted.
- Do not touch `_escalation_excerpt`, any `_write_session` call, the sidecar's `escalation` record, or the escalation prompt — the only `agents.py` surface this task touches is `EscalationError`'s declaration and its four raise sites, setting `path`.
- Do not surface the escalation's role in the alert — a deliberate decision, not a gap: it is discoverable from the artifact itself.
- Touch `notify.py`, `main.py` (the nine call sites plus the one resumed-escalation raise at `:237`), `runtime.py` (the one call site), `agents.py` (`EscalationError`'s declaration and its four raise sites only), and `tests/test_notify.py` only.
