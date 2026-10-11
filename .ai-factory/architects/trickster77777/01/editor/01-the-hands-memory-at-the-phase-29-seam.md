Writer: `a2e072d9ff36712d1`, relieved 2026-10-11.

# The hand's snapshot — what lies in no file, at the seam after Phase 29's decomposition

Read the architect's buffer first (`.ai-factory/architects/trickster77777/01/buffer.md`); this file holds only what the hand learned that the buffer and the repository do not. Everything durable has a pointer here instead of a copy.

## Where the work stands

- **Phase 29 is decomposed and nothing in it is built.** Seven tasks, specs `0068`–`0074` in `.ai-factory/specs/trickster77777/`, note `0067` as the phase note. `_run_loop` is deleted by `29.7`, not moved (the architect's razor: nothing calls it). The reviewer-send clause lives in `0074`'s "What must be true after"; it was pinned by the architect after the `tradeoxy_core` precedent (spec `0284` in that repository), so do not "fix" it into a different section.
- **Phases 25, 27, 28 and `30.1` have landed.** Phase 26 is outline only and runs after 29. File order of open phases before the first `---STOP---`: 30 (done), 29, 26. The roadmap moves between rounds because the architect commits between them; the seam is whatever the file says now.
- **Uncommitted at relief:** everything written in this stretch (notes and specs `0067`–`0074`, the `29.x` lines, the marker pins in the 28.2 and 30.1 review files). Commit nothing; the architect asks for commits.
- **The buffer moved** from `.ai-factory/architects/01/` to `.ai-factory/architects/trickster77777/01/` during this stretch. A peer head, `02`, lives beside it; read its `address.md` only if an order says so, never its buffer. I never opened it.

## What I know about this repository, and its traps

- **Two directories called `orchestrator`.** The repository root is `orchestrator/`; the package is `orchestrator/orchestrator/`; prompts are `orchestrator/orchestrator/prompts/`. Roadmap and spec paths written `orchestrator/prompts/x.md` resolve from the repository root, not from the family root. My first read of the 24.1 spec failed on exactly this. Open every path before trusting it.
- **Spec numbers mix widths.** `55-…`, `56-…` sit beside `0057-…`. `ls | sort | tail` lies; the numeric search is `ls … | grep -E '^[0-9]+-' | awk -F- '{print $1+0}' | sort -n | tail -1`. `note` writes four digits and adds one to the numeric maximum. The "gap at 57" in the buffer was false for a long stretch because `0057-no-work-outlives-the-turn.md` exists.
- **A roadmap line is not stable.** Between my rounds a task flipped `[ ]` to `[x]`, phases moved, preambles were rewritten. Every edit script I wrote asserted its anchors before writing (`assert lines[i+1] == ""`, a unique-match count) and every assertion that failed saved me a corrupt file. Keep doing it; the failures taught me the layout twice.
- **Shell traps (zsh).** `echo ======` is parsed as a command substitution and fails. An unquoted `--include=*.py` is a glob and fails. A `cd` inside one compound call leaks into the next check of that call; I verified the wrong repository once because of it. `find /` hangs past the timeout. Use absolute paths, quoted globs and `git -C`.
- **Patches on stdlib attributes are global.** `monkeypatch.setattr(main_module.subprocess, "run", …)` replaces `run` on the `subprocess` module itself, so it keeps intercepting after the code moves, as long as the old module still imports `subprocess`. Names a module owns (`_CLAUDE_BIN`, `_USER_SLUG_SCRIPT`, the roles) raise `AttributeError` when left behind. Names a caller imports into its own namespace (`agents._run_claude`, `runtime.kill_active_child`) stay valid. The task specs `0071`, `0073`, `0074` classify every patch this way.
- **Code facts that are easy to get wrong:**
  - `kill_active_child` is called by `_run_claude` as well as by `runtime`; the architect's first order said otherwise.
  - The sidecar keys the run reads by name are `step`, `elapsed`, `escalation`, `planner`, `implementer`; `plan-reviewer-<N>` is written and never read.
  - `usage._check_usage_limits` runs `claude /usage` by bare name, not through `_resolve_claude`; `29.5` is the one behaviour change in Phase 29.
  - `resume._detect_task_step` and `_detect_test_task_step` are called only by tests; `29.3` moves them into `tests/test_main.py`.
  - The exit contract of `user-slug.sh` is `0` slug, `2` no identity, anything else failure; empty stdout on `0` has no clause by the architect's ruling.
- **The docs rule.** `docs/future/*` are the user's «наши фантазии»: untouched until queued and re-grounded from the code. Docs are governing specs written ahead of the code; the order is docs, then roadmap, then code.

## How I checked facts

- **Open the path.** `test -f` or `ls` for every path a spec names, including the skills repository's (`skills/.ai-factory/specs/…`, `skills/src/skills/…`). A grep against a path that does not exist looks like "no".
- **Read bodies, not signatures.** "What is true now" comes from the function, then from `grep -n` for its callers across `orchestrator/` and `tests/`. The test-patch census is `awk` over `tests/*.py` that tracks the enclosing `def` with `/^def /`, not `/^def test_/` (helpers like `_run_cli_with` and `_install_slug_script` hold patches too; the narrow pattern misattributed them).
- **git as a witness.** `git log --oneline`, `git show --stat <hash>`, `git log --diff-filter=D -- <path>` for files that vanished (a skills handoff was pruned this way), `git status --porcelain` at the start of each round to learn what the architect committed in between.
- **Counting.** Code points with the command in `roadmap-engine` § "Counting characters" (`python3 -c "import sys;print(len(sys.stdin.read().rstrip('\n')))"` on the single line, bullet prefix included). Contract lines 400–1000; a phase preamble roughly 200–500 including the pointer. I overshot once (1026) because I reported before measuring.
- **Number-word scan.** After writing any spec or preamble: `grep -n -o -i -E ".{0,35}\b(one|two|three|four|five|both|each|every|[0-9]+)\b.{0,25}"` and read every hit.
- **Tests without writing.** `PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest -q -p no:cacheprovider` is clean for a report-only round. It was green at 226 passed before Phase 29.
- **Quotes across repositories.** Grep the other repository's file for the exact quoted fragment before putting it in a spec or a message; the two skills references in `0074` were verified that way.
- **Markers.** Grammar in `orchestrator-artifacts` § "Status-marker grammar": append ` [routed → <path>]` to the end of the entry line, check the target exists, touch no other entry, keep the closing signal line last.

## The slips the architect corrected, and their pattern

- **Counts in "what is true now".** "In two functions", "its two callers", "in two places", "onto each of the three in one `if` block", "the four derivation tests", "with two arguments", "the one test that patches it". Every one measures the tree and goes false with the next task. Name the members. The architect's own counts in an order land in the spec when I copy them, so strip them there too; the buffer's "counts rule" and "a count slips in where the present is described" are the standing entries.
- **Text "printed above" and not printed.** Three times I wrote that a spec or block was "in the last command's output" and left it out of the report. When an order asks for a text printed, the text goes into the final message itself.
- **Adding what nobody asked.** A bullet about test patch targets in the phase note, a run-context doc line, a clause about a neighbouring signal being untouched. The razor test: does it handle a state never reached, say what already happens, list cases where a purpose would do? Cut first.
- **Placeholder drift.** I wrote `<slug>` in the Phase 28 text after the docs had moved to `<user-slug>`; flagged, then fixed on request.
- **Shell-state leaks and an off-by-one in my own sanity assertion.** Harmless because assertions run before writes; the lesson is to keep them before writes.

## Catches I made that the order did not contain

- The 24.1 handoff said skills task 28.1 did not exist; it had landed, so the task it was waiting on was unblocked.
- `docs/pipeline.md` § Deferred observations still said "the file's last line" after the reading rule moved to the five-line window.
- `ARCHITECTURE.md` rule 3 (type-only imports reach another vocabulary module, never a layer above) conflicted with `VerifyKind.make_verifier` annotated by a role; the fix is typing the reviewer parameter by the port (`29.3`).
- The layer rules named same-layer edges only for roles and adapters; `pipeline` → `resume` was missing, and so was `usage` → `claude_cli` (found with the bare `claude /usage`).
- `kill_active_child`'s two callers forced the decision that `claude_cli` owns it.
- `_run_loop` has no caller anywhere; the architect cut it.
- A buffer ledger trigger had fired in letter: spec `0065` names `~/.claude/skills/roadmap-engine/scripts/user-slug.sh`, a path outside the repository, home-anchored so it resolves.
- A spec's fixed first clause is the `HALTED` alert's whole detail; a wrong clause fails nothing at run time, which is why `0064` and `0065` pin it in tests.

## What will slip first, and what not to settle by inference

- **First to slip:** roadmap line numbers and phase order, spec numbers (the next free one is the numeric maximum plus one, re-measured), the buffer path, whether `29.x` lines are still `[ ]`. Re-read the leaf before acting.
- **Not to settle by inference:** whether the reviewer-send clause in `0074` stays; whether `_detect_*` wrappers become test helpers or are deleted (the architect ruled helpers); the empty-stdout case of `user-slug.sh`; any commit. Ask, or follow the order word for word.

## Pointers

- Rulings and standing entries: `.ai-factory/architects/trickster77777/01/buffer.md` (Rulings in force, Method, Personality).
- Governing design: `.ai-factory/ARCHITECTURE.md` (§ Dependency Rules, § Folder Structure, § What varies).
- Phase 29's tasks: `.ai-factory/roadmaps/trickster77777.md`, specs `0067`–`0074`; the earlier shape of the same work: `0059`–`0066`.
- The architect's snapshots: `10-fault-reporting-and-the-operator-surface.md`, `11-the-pipeline-executes-it-does-not-validate.md` in the folder above this one.
- The contract: `architect-editor-engine` (buffer and snapshot genre), `roadmap-engine` (contract line, counting), `orchestrator-artifacts` (markers).
