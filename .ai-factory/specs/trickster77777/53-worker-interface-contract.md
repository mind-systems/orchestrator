# The boundary to a run, as a contract

**Date:** 2026-08-09
**Source:** conversation context (skeleton/TDD split of task `22.3`, per `roadmap-decompose-skeleton`; revised — a run started from the surface is a child process, not a worker inside the application)

## Why this is a separate task

A run started from the surface is a child process, so the surface holds only three things about it: its output stream, its exit status, and the means to end it. That boundary does not exist yet. `22.3` wires it for real, against a real process; before it does, this task states what crosses the boundary, in which direction, and what must hold, as a contract a fake child can prove or disprove — no real subprocess, no production code.

Canon for why this is worth doing before the wiring, not folded into it: a boundary invariant that's wrong fails **silently** — a dropped line, a child killed twice, an orphaned process still running after the application that started it is gone — not with a crash. Exactly the shape a contract-task exists to catch at plan-review instead of in the field.

## The contract

**Child → surface**, exactly two things cross:
1. Its output, line by line, in the order the child produced it.
2. Its exit status, once — carrying enough to tell a self-ended run apart from a stopped one.

The child sends nothing else — no partial state, no progress percentage.

**Surface → child**, exactly one thing crosses: a request to end it. Nothing else — a running child is never paused, resumed, or sent any other signal.

**Stop semantics.** Ending a child does not discard what it already sent — every line received before the stop was issued stays in the record. A second stop request against a child already ending is a no-op: it neither raises nor ends anything a second time. When the application itself closes, every child it started is ended with it — nothing outlives the surface that launched it.

## Deliverable (compiles; scenarios red)

A fake pair standing in for the real wiring:

```python
class FakeRecord:
    """Records what crosses the boundary — the scenarios' assertion surface."""
    def __init__(self):
        self.lines: list[str] = []
        self.exit_status = None   # None while the child is running

    def receive(self, line: str) -> None:
        self.lines.append(line)

    def receive_exit(self, exit_status) -> None:
        self.exit_status = exit_status


class FakeChild:
    """Stands in for a real child process; reacts to stop() exactly as the
    contract requires — lines already sent stay recorded, a second stop is a
    no-op, and a stopped exit is distinguishable from a self-ended one."""
    def __init__(self, record: FakeRecord):
        self.record = record
        self.stop_requested = False

    def stop(self) -> None:
        raise NotImplementedError  # 22.3 fills this against the real process

    def run(self, script: list[str], exit_status) -> None:
        raise NotImplementedError  # 22.3 fills this against the real process
```

`FakeRecord` is fully implemented — it is the assertion surface, not the thing under test. `FakeChild.stop`/`.run` are stubbed; the scenarios below drive them and are red until `22.3`'s real wiring gives the fake (or an equivalent double built against the real child's public shape) a working implementation.

## Scenarios (red)

`tests/test_shell.py` (or wherever the shell module's tests land — this task's call, named plainly in the impl):

- **Lines reach the record in order, and a stop mid-stream loses none already sent.** A child scripted to emit five lines, stopped after the third: `FakeRecord.lines` holds exactly the first three, in that order — never fewer, never reordered.
- **A second stop neither raises nor ends anything twice.** Calling `stop()` twice in a row on the same child raises nothing and produces no second exit status.
- **A self-ended child is distinguishable from a stopped one.** A child whose script runs to completion without `stop()` being called reports an exit status recognizably different from one a stop request ended.
- **A child still running when the application closes is ended with it.** Simulating application close while a child's script has not finished still results in that child's `stop()` having been called exactly once — no child outlives the surface that started it.

## Verify

- `uv run pytest` compiles and runs; the four scenarios above are **red** (`FakeChild`'s stubs raise), every pre-existing test stays **green**.

## What NOT to do

- Do not wire a real subprocess, real process I/O, or touch `agents.py`/`runtime.py`/`main.py` — this task proves the contract against a fake child only; `22.3` does the real wiring.
- Do not widen what crosses the boundary beyond the contract above — no second signal type beyond stop, no partial-state message, no direct widget reference from the fake child.
- Do not implement `FakeChild.stop`/`.run` — `22.3` fills them (or replaces the fake with a thin wrapper over the real process that the same scenarios can still drive).
- Touch the shell module's test file (and, if needed, a small fakes module the tests import) only.
