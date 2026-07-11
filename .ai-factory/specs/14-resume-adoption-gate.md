# Resume adoption gate — adopt in-flight artifacts only

Independent of tasks 12/13 (fixes a live single-user bug on the default layout); together with 13 it closes both halves of the plan-adoption surface — 13 removes cross-user contact, this task removes stale-plan adoption within one queue.

## Current state

`_detect_step` (`resume.py:73-89`) resolves the canonical plan by globbing `plans_dir` for `*-{slug}.md`, picking the **lowest-numbered** match, and adopting its seq, path, and sidecar **unconditionally**. The glob exists for a legitimate reason — an interrupted run resumes while `_next_number` would compute a different seq — but slug is just the slugified milestone title, so a *recurring* milestone title (e.g. a second "Update docs" long after the first) matches the completed first plan. Live incident (single user): the old plan's sidecar carried `step: done` → detector returned `done` → `mark_done` + commit with **zero work performed**. Silent-failure grade: wrong output, no crash.

Title comparison cannot discriminate (same slug ⟺ same title modulo punctuation). The discriminator that can is already a protocol contract — `orchestrator-artifacts` (skills repo): **"tracked artifacts belong to completed tasks, uncommitted ones to failed/in-flight."** The orchestrator commits a milestone's artifacts together with the milestone (`git add -A` + commit, `main.py:96,245`), so:

- plan **tracked and clean** → its milestone completed and was committed → stale for adoption;
- plan **untracked, modified, or staged-but-uncommitted** → in-flight (the `git add -A` before review, `main.py:245`, stages mid-milestone artifacts without committing) → legitimate resume target.

## Change

1. **Gate** — in `_detect_step`'s candidate scan (`resume.py:76-89`): for each slug match, query `git status --porcelain -- <plan file>` (cwd `project_dir`); empty output (tracked + clean) → the candidate is stale, skip it. Adopt the lowest-numbered **surviving** candidate; no survivors → keep the computed `plan_path`/seq (fresh plan). One subprocess call per candidate; candidates are few (slug matches only).
2. **Resume paths that must survive, by construction:**
   - crash after plan write / mid plan-review / mid implement → plan untracked or staged → porcelain non-empty → adopted (today's behavior);
   - crash after review-PASS but before `mark_done`+commit → artifacts staged by `main.py:245` → porcelain shows them → adopted, detector returns `done`, the completion path finishes the milestone (today's behavior);
   - completed milestone, later same-titled milestone → old plan tracked+clean → skipped → fresh plan under the new seq (**the fix**).
3. **Assumption made explicit** — the gate leans on the protocol line above: nothing else commits mid-flight artifacts. A developer hand-committing a half-done milestone's artifacts breaks the discriminator (the plan reads as stale; the orchestrator re-plans instead of resuming) — degraded to re-planning, never to false completion. One sentence in `docs/how-it-works.md` (resume section) states this.
4. **Tests** — the gate is the detector's only git-coupled branch; pin it over tmp git repos in `tests/`: (a) committed clean plan with `done` sidecar + same slug → NOT adopted, fresh plan path returned; (b) untracked plan → adopted; (c) staged-but-uncommitted plan → adopted; (d) two candidates, lower committed-clean, higher in-flight → the higher one adopted (survivor rule, not lowest-overall). Existing detector matrix (specs 08) stays green — those fixtures use untracked files, which the gate adopts, so current assertions hold unchanged.

## Files & types

- edit `orchestrator/resume.py` (`_detect_step` candidate scan)
- add tests in `tests/`
- edit `docs/how-it-works.md` (one sentence, resume section)

## Guards

- **Dispatch table untouched** — sidecar validation (`_validate_sidecar_step`) and the step→(step, counter) mapping stay byte-identical; the gate only filters which plan file is adopted before that machinery runs.
- **Fail open toward re-planning, never toward completion** — any git-status error (not a repo, git missing) → treat the candidate as in-flight (adopt), preserving today's behavior; the gate must never manufacture a `done`.
- No sidecar format change, no new fields — the discriminator is git state, already on disk.

## Verification

- `uv run pytest` green, including the four gate cases and the untouched specs-08 matrix.
- Live repro of the incident: complete a milestone titled X, add a new milestone titled X to the roadmap, run → the orchestrator plans fresh (new seq) instead of instantly marking done.
- Live interrupt: kill mid-implement, rerun → resumes from the same plan as before the change.
