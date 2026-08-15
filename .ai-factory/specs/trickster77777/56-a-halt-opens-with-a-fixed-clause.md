# A halt's message opens with a fixed clause

**Date:** 2026-08-15
**Source:** the audit of `21.3`, which found this twice in its plan-review rounds and correctly deferred it as outside that task's touch-list

## Problem today

Eight sites raise a `HaltError` or one of its two subclasses (`NetworkError`, `RateLimitError`), and `main.py:515` takes `str(e).splitlines()[0]` — the first line of whatever message the exception carries — and hands it to `report(...)` (`:516`) as `HALTED`'s detail. Six of the eight open with a fixed clause; two do not:

- `agents.py:340` (`NetworkError`, no `result` event) — `f"Claude CLI died with no result event, exit code {proc.returncode}\n..."` — fixed.
- `agents.py:344` (`NetworkError`, transport failure) — `f"Claude CLI reported a transport failure, exit code {proc.returncode}\n..."` — fixed.
- `agents.py:350` — `RateLimitError(result_text)`. The whole message *is* `result_text`, the agent's own result text — there is no fixed clause to cut to.
- `main.py:137` (no git identity for a named roadmap) — a single literal string, "roadmap_path is 'my' but no git identity is set — set git user.email or user.name, or use an explicit roadmap_path." — fixed.
- `main.py:152-155` (named-roadmap owner mismatch) — `f"Named roadmap {relpath} owner line ({first_line!r}) does not match the current git identity ({expected_owner!r})."`, one line carrying `relpath` (a path under `.ai-factory/roadmaps/`) and the roadmap file's own first line, quoted.
- `main.py:321` (resume past `max_iterations`) — `f"Resume at iteration {impl_start} exceeds max_iterations ({max_iterations}). Raise max_iterations in orchestrator.json to continue."` — fixed; the two substitutions are counts, not a path or agent text.
- `usage.py:48` (session usage threshold) — `f"Session usage at {session_pct:.0f}% — stopping (threshold: {session_threshold:.0f}%)."` — fixed.
- `usage.py:52` (weekly usage threshold) — the same shape — fixed.

`main.py:515`'s cut protects the alert only where the first line already happens to be a summary clause. At `agents.py:350` and `main.py:152-155` it isn't one: the agent's raw result text, or a filesystem path plus a quoted line from a project's roadmap, reaches `HALTED`'s detail whole.

This is newly a defect, not dirt `21.3` should already have swept: `docs/concepts/fault-handling.md`'s invariant 5 read "It names where the account is and its detail is bounded regardless of what produced it" until `21.3` rewrote it to "Its detail is a short fixed label or nothing, whatever produced the outcome." Both sites complied with the rule as it stood when they were written; neither complies with the rule as it now reads.

## The change

Reshape only the two offenders — `main.py:515` and every compliant site stay exactly as they are.

`RateLimitError` at `agents.py:350` gains a fixed first line and carries the result text below it, in the same shape `NetworkError`'s two sites already use:

```python
raise RateLimitError(f"Agent reported a rate limit\n{result_text}")
```

The named-roadmap owner-mismatch `HaltError` at `main.py:152-155` opens with a fixed clause naming what went wrong, moving the path and the quoted owner line to a second line:

```python
raise HaltError(
    f"Named roadmap owner line does not match the current git identity\n"
    f"{relpath}: {first_line!r} vs. expected {expected_owner!r}"
)
```

Both now follow the convention the other six sites already establish, stated once for every future halt: a halt's message opens with a fixed clause naming what happened, and anything variable — a path, a quoted line, an agent's own text, captured output — goes on a later line. The first-line cut in `main.py:515` is what turns that opening clause into the alert's whole detail; the convention is therefore what the alert's guarantee actually rests on, not an accident of where a message's first newline happens to fall.

## Guards

- `compose()`, `report()`, `_WORDS`, `_ALERT_TYPES`, and spec `54`'s per-outcome detail rule are untouched — this task changes what two exceptions say, never how a notification is built or which outcome carries which detail.
- The six compliant sites (`agents.py:340`, `:344`, `main.py:137`, `:321`, `usage.py:48`, `:52`) keep their messages exactly as they are.
- The console keeps printing the whole message — `main.py:513` prints `str(e)` in full via `f"HALTED — {e}"`, so the path and the quoted line stay visible there; only the alert's detail changes.
- No new exception type and no new field on `HaltError` — both reshaped sites stay `RateLimitError`/`HaltError` exactly as declared today.

## Tests

`tests/test_agents.py` and `tests/test_main.py`, one case each, in the existing style:

- `tests/test_agents.py` — construct the reshaped `RateLimitError` (or drive the code path that raises it) and assert `str(e).splitlines()[0] == "Agent reported a rate limit"`, with the original `result_text` present on a later line.
- `tests/test_main.py` — construct the reshaped owner-mismatch `HaltError` (or drive `_resolve_roadmap_relpath` to raise it) and assert `str(e).splitlines()[0]` is the fixed clause, with `relpath` and the quoted owner line present on a later line.

Why these two and not the other six: a wrong first line here produces a wrong `HALTED` alert and nothing crashes — the only kind of surface this project writes tests for. The six compliant sites carry literal one-line strings with nothing to get wrong; there is no cut to test because there is nothing after the cut.

## Verify

- `uv run pytest` green, including the two new cases.
- Read all eight sites and confirm every first line is now a fixed clause — the six unchanged plus the two reshaped.
- Manual trace of both reshaped halts: the `HALTED` alert's detail is the fixed clause alone, while the console (`main.py:513`) still prints the whole message, path and quoted line included.

## What NOT to do

- Do not touch `compose()`, `report()`, or spec `54`'s detail rule.
- Do not reshape the six compliant messages.
- Do not add a field to `HaltError` or introduce a new exception type.
- Do not remove the path or the quoted line from the console output — `main.py:513` keeps printing `str(e)` in full.
- Touch `orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, and `tests/test_main.py` only.
