# Plan Review: 21.4 — A halt's message opens with a fixed clause (round 2)

## Code Review Summary

**Files Reviewed:** 1 plan + 8 source/test/doc files re-verified against it (`orchestrator/agents.py`, `orchestrator/main.py`, `orchestrator/usage.py`, `orchestrator/notify.py`, `tests/test_agents.py`, `tests/test_main.py`, `docs/concepts/fault-handling.md`, `docs/features/named-roadmaps.md`)
**Risk Level:** 🟢 Low

### Context Gates

- **Architecture** — `.ai-factory/ARCHITECTURE.md` present. No boundary or dependency change: `agents.py` declares the exception hierarchy and owns the `RateLimitError` raise site; `main.py` owns roadmap resolution. `usage.py` imports `HaltError` from `agents.py` and is read-only in this plan; `notify.py` never sees the exception, only the composed detail. **PASS**.
- **Rules** — `.ai-factory/RULES.md` does not exist in this project. **WARN** (missing optional file; nothing to check against).
- **Roadmap** — `.ai-factory/roadmaps/trickster77777.md` carries `21.4` unchecked under Phase 21, whose `Governing spec:` is `docs/concepts/fault-handling.md`. Its `Spec:` tag resolves to `.ai-factory/specs/trickster77777/56-a-halt-opens-with-a-fixed-clause.md`. **PASS**.
- **Governing spec conformance** — invariant 5 of `docs/concepts/fault-handling.md:93` reads verbatim as the plan quotes it ("A notification is a signal, not the account. Its detail is a short fixed label or nothing, whatever produced the outcome."). Both reshapes serve it directly. **PASS**.
- **Task-spec conformance** — every *Guard* and every *What NOT to do* clause from spec `56` is carried into the plan as an explicit constraint or an explicit unchanged-check: no new type, no new field, no truncation of `result_text`, the six compliant sites untouched, `compose()`/`report()`/`_WORDS`/`_ALERT_TYPES` untouched, `main.py:513` keeps printing `str(e)` in full, touch-list held to the four named files. **PASS**.

### Round-1 findings: all three resolved

| Round-1 finding | Resolution in this revision |
|---|---|
| 1. Task 4 hand-rolled a conditional `state.active_proc` reset instead of the existing fixture | Plan line 52 now mandates `clean_active_proc` **unconditionally**, names the fixture's coordinate (`tests/test_agents.py:449`), cites the four neighbouring cases that request it (`:466`, `:473`, `:489`, `:525`), and explicitly bans both the hand-rolled reset and the conditional. ✓ |
| 2. Task 6 verified `notify.py` without listing it | Plan line 64 now lists `orchestrator/notify.py` (read-only) alongside `orchestrator/usage.py` (read-only). ✓ |
| 3. Task 5's census of existing tests reaching `main.py:152` was short by one | Plan line 59 now names both `test_resolve_roadmap_relpath_my_owner_mismatch_raises_halt` (`:1139`) and `test_resolve_roadmap_relpath_my_malformed_first_line_raises_halt` (`:1151`), with the reason `:1151` reaches the same guard. ✓ |

### Verified against ground truth (re-checked this round, not carried over)

| Plan's claim | Verified |
|---|---|
| `agents.py:150-151` — `HaltError` docstring, one line | ✓ `class HaltError(Exception):` / `"""An operational halt that is not a task failure — 🟡."""` |
| `agents.py:350` — `raise RateLimitError(result_text)` | ✓ exact |
| `agents.py:340`, `:344` — the two `NetworkError` shapes to mirror | ✓ both open with a fixed clause, variable text on line 2 |
| `main.py:137`, `:152-155`, `:321` | ✓ exact, including the `f"Named roadmap {relpath} owner line ({first_line!r}) …"` single line |
| `usage.py:48`, `:52` | ✓ exact |
| `main.py:511-517` — `except HaltError`, `:513` full print, `:515` first-line cut | ✓ exact |
| The census is exactly eight sites | ✓ `grep` over `orchestrator/` finds `HaltError`/`NetworkError`/`RateLimitError` raises at precisely those eight coordinates and nowhere else |
| `notify.py` carries `_WORDS` (`:37`), `_ALERT_TYPES` (`:48`), `compose()` (`:60`), `report()` (`:69`) | ✓ all four exist as named |
| `tests/test_agents.py:449` `clean_active_proc` fixture; `:541` `_classify_result` header; `:593` ratelimit-text case | ✓ |
| `RateLimitError` absent from `tests/test_agents.py`'s import block (`:13-27`) | ✓ — `HaltError` and `EscalationError` are there, `RateLimitError` is not |
| `tests/test_main.py:1139`, `:1151` — both bare `pytest.raises(HaltError)`, no `match=` | ✓ both keep passing after the reshape |

Behavioural checks that matter and hold:

- **Task 4 reaches `ratelimit` on attempt 1, with no retry sleep.** With `returncode = 1` and `result_text = "You hit your limit, resets at 5pm"`: `_is_overloaded` false (no "overloaded"/"529"), `_is_transport_fault` false (none of the six `_TRANSPORT_MARKERS` at `agents.py:97-104` appear), `parsed_final` truthy so `no_result` false, then `agents.py:139` fires on `"hit your limit"`. `time.sleep(RETRY_DELAY)` at `:335` is never entered — the plan's claim is exact.
- **The fake process surface is complete.** `_run_claude` touches only `.stdout` (iterated, `agents.py:283`), `.wait()` (`:303`), and `.returncode` (`:326`) on the Popen object before the ratelimit raise. The three members the plan specifies are the three that exist.
- **`_CLAUDE_BIN` is the right lever.** `_run_claude` calls `_resolve_claude()` only when the module global is `None` (`agents.py:241`); monkeypatch restores it. Patching `agents.subprocess.Popen` mirrors the file's established idiom (`tests/test_agents.py:532` patches `agents.os.killpg` the same way).
- **`clean_active_proc` is genuinely load-bearing here.** `_run_claude` assigns `state.active_proc = proc` at `agents.py:277` and clears it at `:304` — but `:304` sits *after* the `proc.stdout` iteration, so an exception raised anywhere in the read loop leaves the global set. The new case is the file's only `_run_claude` driver; requesting the fixture unconditionally is correct, and the plan now says so.
- **`result_text` is never empty at the reshaped raise.** `_classify_result` returns `"ratelimit"` only via `agents.py:139`/`:143`, both of which require `"hit your limit"` or `"resets"` in the text — so the second line is never blank.
- **The second line stays one line.** `relpath` is built from a slug and cannot contain a newline; `first_line!r` and `expected_owner!r` are `repr`s, so a newline inside a roadmap's first line renders escaped. `splitlines()[0]` can never leak the variable part.
- **No other consumer reads either message.** `splitlines()[0]` appears only at `main.py:508`, `:515`, `:529`; nothing catches `RateLimitError` to parse a reset time; `tests/test_main.py:923` constructs `RateLimitError("boom")` directly with no dependence on the raise site.
- **`Docs: no` is correct, and now checked positively.** `docs/concepts/fault-handling.md:33` and `:57` are behavioural table rows ("A halt"), not message text. `docs/features/named-roadmaps.md:10` says the mismatch "stops the run with an operational halt naming the owner" — still true after the reshape, since the console (`main.py:513`) prints the whole message and the owner moves to line 2, not out of the message.
- **Task 3 respects the comment discipline.** The docstring the plan describes states behaviour only, with no phase/plan reference and no `.ai-factory/` path — and leaves `RateLimitError`/`NetworkError` docstrings alone rather than triplicating one sentence.

### Critical Issues

None.

### Findings

None. All three round-1 findings are addressed, the touch-list matches spec `56`, the eight-site census is exact, both new cases drive the real raise sites, and no existing test or doc depends on either message's current shape.

### Positive Notes

- **The revision closed each finding at its cause, not at its symptom.** Task 4 does not merely drop the conditional — it names the fixture, its coordinate, the four cases that establish the idiom, and the reason the global needs guarding (`agents.py:277`), so the implementer cannot re-derive the weaker version.
- **The touch-list assumption stays visible.** The Context paragraph still states outright why the convention lands on the `HaltError` docstring rather than in `docs/concepts/fault-handling.md`, and cites the spec clause forcing it — the constraint shapes an architectural choice and is argued, not buried.
- **Task 6 states the negative half of the change.** "The six previously compliant messages are byte-identical to before", plus explicit unchanged-checks on `main.py:511-517` and the four `notify.py` symbols, turns the spec's guards into a step that can fail rather than a hope — and the read-only markers now cover every file the step actually opens.
- **The tests are placed where a regression would actually occur.** The spec permitted reconstructing the strings; the plan drives `agents.py:350` and `main.py:152` themselves, and works out the fake-process surface and the no-sleep property to keep that cheap.

## Deferred observations

- Affects: unknown (a future notification task) — The same first-line cut this task fixes for `HALTED` is applied unchanged to two sibling outcomes, where it still leaks variable text. `main.py:508` cuts `PipelineStopError`'s message for `UNCONVERGED`, and two of its raise sites are single-line messages carrying variable text: `main.py:314` embeds `{seq}-{task.slug}` and `main.py:404` embeds `{task.title}` — a title read out of the project's own roadmap. `main.py:529` does the same for `ERRORED` over any unhandled exception, and `agents.py:358` raises `RuntimeError(f"Claude returned error: {result_text[:500]}")` — a single line of up to 500 characters of the agent's own text, which reaches the alert whole. Invariant 5 of `docs/concepts/fault-handling.md` is written about notifications generally, not about halts specifically, so the same defect class is live on the sibling outcomes. Correctly out of scope here: spec `56` scopes itself to `HaltError` and its subclasses, and its *What NOT to do* pins the touch-list to four files.
- Affects: a future docs task on `docs/concepts/fault-handling.md` — After this task, the convention "a halt's message opens with a fixed clause, everything variable below it" lives only in a Python docstring on `HaltError`. The docs tier carries the invariant the convention serves (invariant 5, `:93`) but not the convention itself, so a reader working from `docs/concepts/fault-handling.md` learns what the notification must not contain without learning the message shape that guarantees it. Out of scope here: spec `56` restricts the touch-list to `orchestrator/agents.py`, `orchestrator/main.py`, `tests/test_agents.py`, `tests/test_main.py`, and the plan records that constraint rather than working around it.
- Affects: task 23.1 — `tests/test_agents.py` still carries two plan-layer coordinates as section dividers: `# Task 4: kill_active_child no-op branches` (`:462`) and `# Task 6: kill_active_child killpg-failure fallback` (`:506`). They sit in a file this task touches, so an implementer adding a case nearby has the wrong pattern in view; but renaming them is unrelated to reshaping two halt messages, and Phase 23 settles that this coordinate is removed at the source (the planner and implementer prompts) rather than policed downstream. Its guard is explicit that no existing `# Task N:` heading is swept.

PLAN_REVIEW_PASS
