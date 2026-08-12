# Plan Review: 21.1 — A result-bearing transport error is transient, not a verdict

**Plan:** `.ai-factory/plans/trickster77777/14-21-1-a-result-bearing-transport-error-is-transient-not-a-verdict.md`
**Task spec:** `.ai-factory/specs/trickster77777/41-transport-fault-is-not-a-verdict.md`
**Governing spec:** `docs/concepts/fault-handling.md`
**Risk Level:** 🟢 Low

## Context Gates

- **Architecture** (`.ai-factory/ARCHITECTURE.md`) — OK. The change stays inside the Agents layer (`orchestrator/agents.py`) and its test file: no new module, no new import, no change of dependency direction, no step-selection logic leaking into `agents.py`. Two private module-level predicates beside `_classify_result` match the file's existing shape (`_has_signal`, `_escalation_excerpt`, `_sorted_nvm_node_dirs`). No `## Features` row is owed — that table (`:123-135`) is roadmap-prune's, keyed by commit hash.
- **Rules** (`.ai-factory/RULES.md`) — WARN: file absent in this project (`.ai-factory/` holds `ARCHITECTURE.md`, `orchestrator.json`, and the artifact directories only); gate skipped.
- **Roadmap** — OK. `.ai-factory/roadmaps/trickster77777.md:113` carries the unchecked `21.1` contract line under `### Phase 21 — A fault the run can report`; the plan's title matches it verbatim and its `Spec:` tag resolves to the spec the plan reads. The phase's governing spec `docs/concepts/fault-handling.md` was walked to the leaf: its known-faults table (`:32`) already states present-tense that *"a transport failure that arrives carrying its own error text"* is *"handled identically to a transport failure that arrives with no answer at all"*, and Invariant 1 (`:89`) that *"a transport failure is never a verdict"*. The doc leads the code, so **Docs: no** is the correct call, not an omission. Nothing under `docs/` quotes either operator-facing string, so no reference page is owed a value update either.
- **skill-context** (`.ai-factory/skill-context/aif-review/SKILL.md`) — absent; no project overrides to apply.

## Review-1 finding: closed

Plan-review 1 raised one finding — Task 4 would append five never-red cases directly beneath a block header (`tests/test_agents.py:540-547`) that still claims *"Red against the `NotImplementedError` stub … a follow-up task fills in"*, a statement false since 18.1.2 and a plan-layer citation the repo forbids in test comments. The plan now opens Task 4 with the rewrite, quotes the replacement header verbatim, scopes it to text only, explicitly preserves the deliberate `# Task N:` cross-repo citations (verified: 17 of them remain in this file, exactly the set `36-test-agents-stale-red-docstring.md` deferred) and the six `"Row N:"` docstrings, and adds a matching Verify line. Correctly addressed.

## Ground-truth verification

Every coordinate the plan cites was re-checked against the files as they stand:

| Plan claim | Verified |
|---|---|
| `_classify_result` at `agents.py:92-120`; overload branch `:106`; `no_result` pair `:108-111`; ratelimit `:112`; `returncode != 0 → "error"` `:114` | ✅ exact |
| `_write_session` ends at `:89` — the insertion point for the two predicates | ✅ |
| `NetworkError` at `:131-133`, a `HaltError` subclass | ✅ |
| `_run_claude` dispatch `:298-341`; retry print `:300-306`; `network_halt` raise `:308-312`; `[:500]` cut at `:323` | ✅ |
| `result_text = parsed_final.get("result", "")` at `:295` | ✅ |
| `MAX_RETRIES`/`RETRY_DELAY` at `:39-40` | ✅ |
| `main.py:511-516` takes `str(e).splitlines()[0]` and sends that one line | ✅ — `except HaltError` at `:511`, the cut at `:515`, `notify(..., "stop")` at `:516`; a `NetworkError` reaches it and exits 0 |
| `_classify_result` imported at `tests/test_agents.py:19`; block header `:540-547`; six cases `:550-577` | ✅ |

Branch-order trace of the proposed classifier over the whole table:

- Incident text, exit 1, attempt 1/3 → new branch 1 → `"retry"` (today: `"error"` → bare `RuntimeError` on the first attempt). The defect the task exists for is closed.
- Same text, attempt 3/3 → new branch 2 → `"network_halt"` → `NetworkError` → 🟡 halt, exit 0, resumable.
- `("boom", rc=1)` → past both new branches to `:114` → `"error"`. A markerless nonzero exit is untouched.
- `("You hit your limit", rc=1)` → no marker → `"ratelimit"`. Untouched.
- `("handles connection reset", rc=0)` → both new branches gated by `returncode != 0` → `"ok"`. (Checked the near-miss: `"resets"` is *not* a substring of `"connection reset"`, so the ratelimit test does not fire here either.)
- `parsed_final == {}` → `result_text == ""` → new branches inert → the `no_result` pair answers exactly as today. Disjointness holds by construction.
- `{"result": ""}`, rc=1 → non-empty dict, empty text → no marker, `no_result` False → `"error"`, exactly as today.

Both operator-facing splits are exhaustive over the verdicts that can reach them:

- **Retry print.** `"retry"` can only be reached from the overload branch, the `no_result` branch, or the new transport branch. An overload retry cannot have `parsed_final == {}` (an empty dict yields `result_text == ""`, which `_is_overloaded` rejects), so the `not parsed_final` arm is unambiguous and the `_is_overloaded` → transport ordering below it mirrors the classifier's own precedence. No retry path prints unlabelled.
- **`NetworkError` message.** `"network_halt"` can only be reached from the `no_result` branch (`parsed_final` empty) or the new transport branch (`parsed_final` non-empty), so the `not parsed_final` split is total, and the new first line is the one `main.py:515` delivers.

The five pinned test cases were each evaluated by hand against the proposed branch set; all five return the asserted literal, and none of the six existing cases changes its answer.

## Critical Issues

None.

## Positive Notes

- **The supersession is named, scoped, and justified.** Exactly one clause of `31-network-cli-death-retry-then-halt.md` is overridden, with the reason its premise no longer holds; that spec's other pins stand. A conflicting earlier pin surfaced rather than silently contradicted is the right move.
- **The `returncode != 0` conjunct is defended, not assumed.** `result_text` is the agent's *own* final message, so a successful plan or review discussing this very task would otherwise reclassify as `"retry"` and silently re-run a multi-hour step. The plan states the failure mode in the code's own terms and pins it with a test.
- **Disjointness from the `no_result` pair is proved, not hoped for** — `parsed_final == {}` ⇒ `result_text == ""` ⇒ no marker is a substring — which is why the branch position can be asserted with confidence.
- **The operator-facing strings are treated as behaviour.** Recognising that `main.py:515` delivers only the first line of the exception, and therefore that the first line *is* the report, is the seam a plan of this size usually misses.
- **Verify is falsifiable and honest about its limits** — it says outright which two strings are checked by trace rather than by assertion, and why asserting them would mean driving the CLI.
- **Task 4 fixes the stale header before appending under it**, so the diff leaves the block in one present-tense voice instead of widening a false claim by five cases.

## Deferred observations

- Affects: `tests/test_agents.py` module docstring (`:1-2`) — the file's opening docstring still enumerates its covered surfaces as *"_has_signal, TestRunner._extract_test_command, _resolve_claude, sidecar session I/O (_read_sessions/_write_session), and kill_active_child"*, an enumeration already incomplete since the `_classify_result` and escalation blocks landed. This task neither creates the drift nor changes its kind — the five new cases extend a surface the docstring already omits — and correcting it means cataloguing surfaces contributed by several unrelated tasks, which is a test-file-hygiene task of its own rather than part of 21.1.
- Affects: `_classify_result` branch order, `orchestrator/agents.py:112` — the ratelimit test matches the bare substring `"resets"`, and the new transport branches sit ahead of it, so a hypothetical text reading `"connection resets"` (or one naming both a drop and a limit) would classify as a transport fault rather than a rate limit. Both outcomes are `HaltError`/🟡, no observed message has that shape, and the spec pins this ordering deliberately; worth revisiting only if the rate-limit markers are ever tightened.

PLAN_REVIEW_PASS
