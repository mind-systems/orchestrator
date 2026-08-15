# Plan Review: 21.4 — A halt's message opens with a fixed clause

## Code Review Summary

**Files Reviewed:** 1 plan + 6 source/test files verified against it (`orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/usage.py`, `orchestrator/notify.py`, `tests/test_agents.py`, `tests/test_main.py`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture** — `.ai-factory/ARCHITECTURE.md` present. No boundary or dependency change: both edits stay inside modules that already own these exceptions (`agents.py` declares the type hierarchy, `main.py` owns roadmap resolution). `usage.py` imports `HaltError` from `agents.py` and is untouched. **PASS**.
- **Rules** — `.ai-factory/RULES.md` does not exist in this project. **WARN** (missing optional file; nothing to check against).
- **Roadmap** — `.ai-factory/roadmaps/trickster77777.md:117` carries `21.4` unchecked, and its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/56-a-halt-opens-with-a-fixed-clause.md`, which the plan reads correctly. **PASS**.
- **Spec conformance** — every guard in the spec's *Guards* and *What NOT to do* is carried into the plan verbatim or as an explicit "unchanged" check (no new type, no new field, no truncation of `result_text`, the six compliant sites untouched, `compose()`/`report()`/`_WORDS`/`_ALERT_TYPES` untouched, console keeps printing `str(e)` in full). **PASS**.

### Verified against ground truth

Every coordinate in the plan was checked against the files, not taken on trust:

| Plan's claim | Verified |
|---|---|
| `agents.py:150-151` — `HaltError` docstring | ✓ `class HaltError(Exception):` / `"""An operational halt that is not a task failure — 🟡."""` |
| `agents.py:350` — `raise RateLimitError(result_text)` | ✓ exact |
| `agents.py:340`, `:344` — the two `NetworkError` shapes to mirror | ✓ both open with a fixed clause, variable text on line 2 |
| `main.py:137`, `:152-155`, `:321` | ✓ exact |
| `usage.py:48`, `:52` | ✓ exact |
| `main.py:511-517` — the `except HaltError` arm, `:513` full print, `:515` first-line cut | ✓ exact |
| `tests/test_agents.py:541` — `_classify_result` section header | ✓ |
| `tests/test_agents.py:593` — ratelimit-text case | ✓ |
| `tests/test_main.py:1139` — `test_resolve_roadmap_relpath_my_owner_mismatch_raises_halt` | ✓ |

Behavioural checks that matter and hold:

- **Task 4's fake process is sufficient.** `_run_claude` touches exactly `.stdout` (iterated), `.wait()`, and `.returncode` on the Popen object — the three members the plan specifies. Nothing else is needed.
- **Task 4's classification reaches `ratelimit` on attempt 1.** With `result_text = "You hit your limit, resets at 5pm"` and `returncode = 1`: `_is_overloaded` is false (no "overloaded"/"529"), `_is_transport_fault` is false (no marker matches), `parsed_final` is truthy so `no_result` is false, and the `returncode != 0 and "hit your limit"` branch fires. No `time.sleep(RETRY_DELAY)` is entered — the plan's claim is correct.
- **`monkeypatch.setattr(agents, "_CLAUDE_BIN", ...)` is the right lever.** `_run_claude` calls `_resolve_claude()` only when the module global is `None`, and monkeypatch restores it afterwards.
- **No existing test breaks.** `tests/test_main.py:923` builds `RateLimitError("boom")` directly (no dependence on the raise site); the two `_resolve_roadmap_relpath` cases that reach `main.py:152` both use a bare `pytest.raises(HaltError)` with no `match=`. `RateLimitError` is already imported in `tests/test_main.py:13` and is genuinely absent from `tests/test_agents.py`'s import block, as Task 4 says.
- **The second line stays one line.** `relpath` cannot contain a newline, and `first_line!r`/`expected_owner!r` are `repr`s — a newline inside the roadmap's first line would render escaped, so `splitlines()[0]` can never leak the variable part.
- **No doc quotes either message.** `grep` over `docs/` finds only the two behavioural table rows in `fault-handling.md` (`:33`, `:57`), which describe *what the run does*, not the message text. `Docs: no` is correct.

### Critical Issues

None. Both reshapes are correct, the touch-list matches the spec, and the two new cases drive the real raise sites rather than reconstructing strings.

### Findings

**1. Task 4 hand-rolls cleanup that an existing fixture already does — and makes it conditional.** (`tests/test_agents.py`)

The plan says "reset `agents.state.active_proc` if the case leaves it set". The file already has the fixture for exactly this, three sections above the insertion point:

```python
# tests/test_agents.py:450
@pytest.fixture
def clean_active_proc():
    """Reset the shared state.active_proc global to None before and after each
    test — it's a module-level global, not per-instance, so leftover state would
    silently corrupt unrelated tests."""
```

Two problems with the plan's phrasing. First, it ignores the established idiom — four neighbouring tests (`:466`, `:473`, `:489`, `:525`) request `clean_active_proc`, and the new case is the only one in the file that will drive `_run_claude`, which assigns `state.active_proc` at `agents.py:277`. Second, "if the case leaves it set" invites the implementer to check once and skip cleanup: on the happy path `agents.py:304` clears it before the raise, so the check comes back "no" and nothing is added — leaving the file's one `_run_claude`-driving test as the only unguarded writer of that global. The fixture is unconditional and costs one parameter. Task 4 should say: request the `clean_active_proc` fixture alongside `monkeypatch` and `tmp_path`, and drop the conditional reset.

**2. Task 6 asks the implementer to verify a file it does not list.** (plan, Task 6)

Task 6's body requires confirming "`compose()`, `report()`, `_WORDS`, `_ALERT_TYPES` in `notify.py`" are unchanged, but its `Files:` line names only `orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/usage.py` (read-only). `orchestrator/notify.py` should be added to that line with the same `(read-only)` marker that `usage.py` carries — otherwise the file the check is *about* is the one file the task does not admit to opening. (`notify.py` is outside the spec's touch-list, so the read-only marker is what keeps it honest.)

**3. Task 5's census of existing tests reaching the reshaped raise is short by one.** (plan, Task 5)

The plan says "Leave the existing mismatch case untouched — it asserts only the exception type (no `match=`), so it keeps passing." Two existing cases reach `main.py:152`, not one: `test_resolve_roadmap_relpath_my_owner_mismatch_raises_halt` (`tests/test_main.py:1139`) and `test_resolve_roadmap_relpath_my_malformed_first_line_raises_halt` (`tests/test_main.py:1151`, which writes `"# Not an owner line"` and so fails the same `first_line.strip() != expected_owner` guard). The conclusion survives — both are bare `pytest.raises(HaltError)` and both keep passing — but an implementer told to check "the existing mismatch case" singular will not look at `:1151`. Name both.

### Positive Notes

- **The touch-list assumption is recorded, not silently taken.** The plan's Context paragraph states outright why the convention is stated on the `HaltError` docstring rather than in `docs/concepts/fault-handling.md`, and cites the spec clause that forces it. That is the right way to handle a constraint that shapes an architectural choice — visible to the reviewer instead of buried in an omission.
- **Task 4 drives the raise site instead of reconstructing the string.** The spec permitted either ("construct the reshaped `RateLimitError` (or drive the code path that raises it)"); the plan chose the one that would actually catch a regression at `agents.py:350`, and worked out the fake-process surface and the no-sleep property to make it cheap.
- **Task 6 states the negative half of the change.** "The six previously compliant messages are byte-identical to before" and the explicit `main.py:511-517`/`notify.py` unchanged-checks turn the spec's guards into a verifiable step rather than a hope.
- **Task 3 is scoped correctly.** Stating the rule once on the base class and explicitly leaving `RateLimitError`/`NetworkError`'s docstrings alone ("the rule is inherited, not restated") is the right call — the alternative drifts three copies of one sentence.

## Deferred observations

- Affects: unknown (a future notification task) — The same first-line cut that this task fixes for `HALTED` is applied unchanged to two other outcomes, where it still leaks variable text. `main.py:508` cuts `PipelineStopError`'s message for `UNCONVERGED`, and two of its four raise sites are single-line messages carrying variable text: `main.py:314` embeds `{seq}-{task.slug}` and `main.py:404` embeds `{task.title}` — a title read out of the project's own roadmap. `main.py:526-528` does the same for `ERRORED` over any unhandled exception, and `agents.py:358` raises `RuntimeError(f"Claude returned error: {result_text[:500]}")` — a single line of up to 500 characters of the agent's own text, which reaches the alert whole. Invariant 5 of `docs/concepts/fault-handling.md` ("never a filesystem path, never a line an agent wrote") is written about notifications generally, not about halts specifically, so the same defect class is live on the sibling outcomes. Correctly out of scope here: spec `56` scopes itself to `HaltError` and its subclasses, and its *What NOT to do* pins the touch-list to four files.
- Affects: a future docs task on `docs/concepts/fault-handling.md` — After this task, the convention "a halt's message opens with a fixed clause, everything variable below it" lives only in a Python docstring on `HaltError`. The docs tier carries the invariant the convention serves ("Its detail is therefore a short fixed label or nothing at all"), but not the convention itself, so a reader working from `docs/concepts/fault-handling.md` learns what the notification must not contain without learning the message shape that guarantees it. Out of scope here: spec `56` explicitly restricts the touch-list to `orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, `tests/test_main.py`, and the plan records that constraint rather than working around it.
- Affects: the phase-19 durable–plan boundary work described in the Phase 21 note — `tests/test_agents.py` still carries two plan-layer coordinates as section dividers: `# Task 4: kill_active_child no-op branches` (`:462`) and `# Task 6: kill_active_child killpg-failure fallback` (`:506`). They sit in a file this task touches, so an implementer adding a case nearby has the wrong pattern in view; but renaming them is unrelated to reshaping two halt messages, and the Phase 21 note settles that this coordinate is removed at the source (the implementer prompt) rather than policed downstream.
