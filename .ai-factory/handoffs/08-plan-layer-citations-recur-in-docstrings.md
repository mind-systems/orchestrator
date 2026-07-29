# Handoff — the plan-citation prohibition landed and the leak continued: docstrings, and three of four actors unbound

> Cross-repo handoff from the Herald side (`~/projects/repo-stats-herald`), 2026-07-29. **Follows up [handoff 05](05-code-cites-plan-layer-orchestrator-side.md)**, whose §4 asked this repo to plant a positive prohibition in the implementer prompt. It was planted — `8753c43`, 2026-07-12, "1.1 — Implementer: forbid plan-layer citations in code and tests". The leak recurred anyway, sixteen days later, and the two reasons are mechanical rather than a matter of the model ignoring an instruction. Nothing in this repo was edited; this is diagnosis plus a recommendation.

## 1. What was found

`roadmap-prune`'s Step 7.5 citation scan — the skills-side warn-only net handoff 05 §3 queued — fired during a full prune of Herald and surfaced three live citations of the plan layer from durable test files:

| File | Cites | Written by | Date |
|------|-------|-----------|------|
| `tests/commits/test_collect.py:8` | `.ai-factory/specs/77-commit-collector-parse-test-plan.md` | `22251fd` — a **test-roadmap** task | 2026-07-29 |
| `tests/commits/test_parse_log.py:9` | the same spec 77 | `22251fd` — same task | 2026-07-29 |
| `tests/versioning/test_versioner.py:3` | `.ai-factory/specs/19-versioning.md` | `0783684` — task 11.1, an ordinary implementer task | 2026-07-28 |

Both spec paths are now dead: the prune deleted spec 19 with its `[x]` line, and spec 77 went with the test roadmap. This is the dangling half of handoff 05 §7's hazard; the false-resolution half is still only a matter of time, since Herald's phase numbers already run to 23 with holes.

The scan working is the one piece of good news here — the skills-side half of the coordinated fix does its job, and it caught this at exactly the arming moment 05 designed it for.

## 2. Why the prompt rule did not hold

Two independent gaps, both verifiable by grep against `orchestrator/prompts/`.

**The rule says "comments"; every violation is a docstring.** `implementer.md` states it twice — the DON'T list (~:108) and Critical Rule 7 (~:128) — and both read *"in durable code/test comments — no `Phase N`, no note number, no `ROADMAP`/`Plan` reference, no `.ai-factory/` path"*. All three findings are module docstrings: the top-of-file `"""…"""` block, which in Python is not a comment and is not a construct the rule names. The word `docstring` appears in none of the four prompt files. Task 11.1 ran with the rule in force and produced a violation anyway — that is the cleanest evidence available that the wording, not the compliance, is what failed.

**Three of four actors are never told.** The prohibition exists only in `implementer.md`. `planner.md`, `test-planner.md`, and `reviewer.md` contain no form of it. Consequences, in the order they bite:

- A planner is free to write a plan step that says "document the three-file split, per spec 77" — and the implementer, following ground truth of the plan, transcribes the citation into the file. The `22251fd` pair came out of a test task, and `test-planner.md` is silent, which is the likeliest path for exactly that pair.
- `reviewer.md` has no gate for it. Its only reachable clause is the general ~:113 — anything in the diff is a finding "down to cosmetics" — and across roughly sixty completed Herald tasks it never once flagged a plan citation. A rule stated to the writer and checked by nobody is unenforced by construction.

## 3. Recommendation

Prompt edits are structural, and handoff 05 §5 plus this repo's own working discipline both say plan in chat and confirm before touching a prompt — so this is a proposal, not a queued change.

1. **Name the construct, don't rely on "comment".** Widen the wording in both `implementer.md` sites to something that cannot be read around — *code and test comments, docstrings, and module headers*. The construct list is what carries the rule; the citation-shape list (`Phase N`, note number, `ROADMAP`/`Plan`, `.ai-factory/` path) is already right and matches the prune scan's grep set.
2. **Bind the plan authors.** `planner.md` and `test-planner.md` need the same prohibition, framed for their altitude: a plan step never instructs the implementer to reference a spec, a note, or a phase from inside a source file. This is the upstream cut — it stops the citation before there is anything to transcribe.
3. **Give the reviewer a gate.** One explicit check beats the general cosmetics clause, because the general clause demonstrably never fired here. The reviewer is the only actor positioned to catch a leak the writer already rationalized.
4. **Keep single-homing.** Handoff 05 §10 pins the rule's authoritative home on the skills side (`src/global/CLAUDE.md` § "Documentation style"), with anything here a pointer rather than a restated copy. Whether that survives contact with four prompts that each need the rule at their own altitude is a real question, and it is the one thing in this handoff worth settling with the user before writing anything — a rule reworded three times in three prompts is exactly the drift 05 §10's alignment target warns about.

## 4. What was already done, and where

Instance fix only, in Herald, this session: all three docstrings rewritten to state the same information self-contained — the three-file test split is now described by what each file covers, and `test_versioner.py` states its own subject without deferring to a spec. `uv run pytest tests/commits tests/versioning` is green, 45 passed. Herald's working tree also carries a completed roadmap prune (62 tasks retired into `ARCHITECTURE.md ## Features`, artifact dirs and completed specs swept, the test roadmap and its eleven test plans deleted). All of it is uncommitted at the time of writing.

Nothing in this repo was touched — no prompt, no code, no config.

## 5. Orientation for whoever picks this up

- **Don't re-diagnose the class.** Handoff 05 §§7–8 hold the cause/amplifier/seam decomposition and the principle, and they are still correct. The number reuse in `roadmap-prune` remains a deliberate property, not a bug to fix.
- **The boundary is still directional.** The plan layer citing itself is fine; the rule is only that nothing outside `.ai-factory/` may cite into it. A widened construct list must not be allowed to read as a ban on phase numbers inside specs.
- **Dates are the argument.** If someone proposes that this is pre-rule residue, the two commit dates settle it: the rule is 2026-07-12, the violations are 2026-07-28 and 2026-07-29.
