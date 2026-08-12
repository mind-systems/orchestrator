# Plan Review: 21.1 — A result-bearing transport error is transient, not a verdict

**Plan:** `.ai-factory/plans/trickster77777/14-21-1-a-result-bearing-transport-error-is-transient-not-a-verdict.md`
**Task spec:** `.ai-factory/specs/trickster77777/41-transport-fault-is-not-a-verdict.md`
**Governing spec:** `docs/concepts/fault-handling.md`
**Risk Level:** 🟢 Low

## Context Gates

- **Architecture** (`.ai-factory/ARCHITECTURE.md`) — OK. The change is confined to the Agents layer (`orchestrator/agents.py`) plus its test file. No new import, no new module, no change to the dependency direction (`agents.py` still imports only `state`), no step-selection logic leaking into `agents.py`. Two new module-level predicates alongside `_classify_result` fit the file's existing shape (`_has_signal`, `_escalation_excerpt`, `_sorted_nvm_node_dirs` are all private module helpers). No `## Features` row is owed — that table is roadmap-prune's.
- **Rules** (`.ai-factory/RULES.md`) — WARN: file absent in this project; gate skipped.
- **Roadmap** — OK. `.ai-factory/roadmaps/trickster77777.md:113` carries the unchecked `21.1` contract line under `### Phase 21 — A fault the run can report`; the plan's title matches it verbatim and its `Spec:` tag resolves to the spec the plan reads. Phase 21's governing spec (`docs/concepts/fault-handling.md`) was walked: its known-faults table already states present-tense that *"a transport failure that arrives carrying its own error text"* is *"handled identically to a transport failure that arrives with no answer at all"*, and Invariant 1 states *"a transport failure is never a verdict"*. The doc leads the code — the plan's **Docs: no** is correct, not an omission.
- **skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`) — absent; no project overrides to apply.

## Ground-truth verification

Every line reference in the plan was checked against the files as they stand:

| Plan claim | Verified |
|---|---|
| `_classify_result` at `agents.py:92-120`; overload branch `:106`; `no_result` pair `:108-111`; ratelimit `:112`; `returncode != 0 → "error"` `:114` | ✅ exact |
| `_write_session` at `:80-89` (insertion point for the two predicates) | ✅ |
| `NetworkError` at `:131-133`, subclass of `HaltError` | ✅ |
| `_run_claude` dispatch `:298-341`; retry print `:300-306`; `network_halt` raise `:308-312`; `[:500]` cut at `:323` | ✅ |
| `result_text = parsed_final.get("result", "")` at `:295` | ✅ — the disjointness argument (`parsed_final == {}` ⇒ `result_text == ""` ⇒ no marker matches) holds |
| `MAX_RETRIES`/`RETRY_DELAY` at `:39-40` | ✅ |
| `main.py:511-516` takes `str(e).splitlines()[0]` and sends that one line | ✅ — `main.py:515` exactly; `NetworkError` reaches it via `except HaltError` (🟡 machine, the correct colour per fault-handling.md) |
| `_classify_result` imported at `tests/test_agents.py:19`; existing block at `:540-577` (six cases) | ✅ |

Branch-order trace of the proposed classifier, over the whole table, confirms the plan's claims:

- Incident text, exit 1, attempt 1/3 → new branch 1 → `"retry"` (was `"error"` → bare `RuntimeError` on the first attempt). The defect the task exists for is closed.
- Same text, attempt 3/3 → new branch 2 → `"network_halt"` → `NetworkError`, a clean 🟡 halt, resumable like any other.
- `("boom", rc=1)` → falls past both new branches to `:114` → `"error"`. A markerless nonzero exit is unaffected.
- `("You hit your limit", rc=1)` → no transport marker → `"ratelimit"`. Unaffected.
- `("handles connection reset", rc=0)` → both new branches gated by `returncode != 0` → `"ok"`. The `returncode != 0` conjunct is genuinely load-bearing, and the plan states why in the code's own terms.
- `parsed_final == {}` → `result_text == ""` → new branches inert → the `no_result` pair answers exactly as today.

The three-way retry print is exhaustive by construction: a `"retry"` verdict can only come from the overload branch, the `no_result` branch (`parsed_final` empty), or the new transport branch — so no retry path can fall through the split unprinted.

## Findings

### 1. `tests/test_agents.py:540-547` — the block header the plan appends under is stale, and Task 4 extends its false claim to five more cases

The `# --- _classify_result ---` block opens with:

```
# Red against the NotImplementedError stub — these pin the decision-table
# contract that a follow-up task fills in; they turn green once the body is
# implemented.
```

`_classify_result` has a full body today (`agents.py:104-120`) and all six cases in that block are green — the comment describes a state two tasks in the past, and it narrates the plan layer (*"a follow-up task fills in"*), which the repo's own discipline forbids in code and test comments. Task 4 appends five cases that were never red *directly beneath it*, so the diff widens a false statement instead of leaving it merely stale.

This is the same defect class the project already fixed once for this very file — `.ai-factory/specs/trickster77777/36-test-agents-stale-red-docstring.md` rewrote a stale RED docstring at `:260-268` for exactly this reason. Its guard deferring *other* comments was scoped to the `# Task N:` citations kept as cross-repo evidence; this header is not one of those.

**Suggested fix, inside the task's existing file boundary** — add to Task 4: rewrite the block's header comment to name what the block groups, in the present tense and with no plan-layer citation, e.g.

```python
# ---------------------------------------------------------------------------
# --- _classify_result ---
# ---------------------------------------------------------------------------
#
# The decision table: which terminal action a finished CLI invocation maps to.
# ---------------------------------------------------------------------------
```

No assertion, test name, import, or fixture changes; `uv run pytest` stays green. Note this also settles the `"Row N:"` docstrings in the block — they index a table that lives only in a task spec, so the five new cases correctly do not adopt that prefix; with the header reworded, the block reads as one present-tense group rather than a half-numbered one.

## Positive Notes

- **The supersession is named, scoped, and justified.** The plan states that it overrides exactly one clause of `31-network-cli-death-retry-then-halt.md` ("do not reclassify a nonzero exit that emitted a `result` event") and leaves that spec's other pins standing. A conflicting earlier pin surfaced rather than silently contradicted is the right move.
- **The `returncode != 0` conjunct is defended, not assumed.** The plan explains that `result_text` is the agent's *own* final message, so a successful plan or review discussing this task would otherwise reclassify as `"retry"` and silently re-run a multi-hour step. That is the non-obvious failure mode of the naive fix, and it is closed by construction and pinned by a test.
- **Disjointness from the `no_result` pair is proved, not hoped for** — `parsed_final == {}` ⇒ `result_text == ""` ⇒ no marker is a substring. This is why branch order can be stated with confidence.
- **The operator-facing strings are treated as behaviour.** Recognising that `main.py:515` delivers only `str(e).splitlines()[0]`, and therefore that the *first* line of the `NetworkError` message is the report, is precisely the kind of seam a plan usually misses.
- **`_is_overloaded` is extracted as behaviour-preserving and correctly takes no new test** — the existing `test_classify_result_overloaded_retry_left` already drives it through the classifier.
- **Doc gate correctly resolved to "no change".** The governing spec already describes the target state; adding prose would have duplicated a fact that already has a home.

## Deferred observations

- Affects: `tests/test_agents.py` module docstring (`:1-2`) — the file's opening docstring still enumerates its covered surfaces as *"_has_signal, TestRunner._extract_test_command, _resolve_claude, sidecar session I/O (_read_sessions/_write_session), and kill_active_child"*, which has been out of date since the `_classify_result` and escalation blocks landed. This task neither creates nor worsens that drift, and correcting it means cataloguing surfaces added by several unrelated tasks — a cleanup for whoever next owns test-file hygiene, not for 21.1.
- Affects: `_classify_result` branch order, `orchestrator/agents.py:112` — the ratelimit test matches the bare substring `"resets"`, and the new transport branches now sit ahead of it, so a hypothetical text reading `"connection resets"` would classify as a transport fault rather than a rate limit. Both outcomes are `HaltError`/🟡 and no observed message has this shape; the spec pins the ordering deliberately. Worth a look only if the ratelimit markers are ever tightened.
