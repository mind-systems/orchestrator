# Handoff — multiuser named roadmaps: the orchestrator's side

## 1. Frame
The multiuser design (per-developer named roadmaps) is ratified and committed in the skills repo — governing spec written, the skill-family work decomposed into its own phase; the orchestrator's half is not started, and this handoff carries everything it needs. The originating session's context isn't available here — trust these files, not memory.

## 2. Read-first map

### Must-read now (minimal rehydration set)
- `~/projects/skills/docs/multiuser-roadmaps.md` — **the governing spec** (Russian): layout, slug derivation, owner line, single-writer invariant, resolution order, what stays flat. Every design question below resolves here; on conflict this file wins.
- `orchestrator/main.py:41,57,344` — `roadmap_filename` is already threaded as a parameter through the implement/test loops; the change extends this existing seam, it does not introduce one.
- `orchestrator/config.py` + the target-project `.ai-factory/config.yaml` — where the new setting lands (the user's decision: the roadmap path is an environment-level setting, configured when the workstation environment is provisioned).

### Read on demand
- `~/projects/skills/.ai-factory/ROADMAP.md` § "Multiuser — named roadmaps" (Phase 4, tasks 4.1–4.5) — the skill-family half of the feature, for coordination context.
- `~/projects/skills/.ai-factory/specs/43-engine-named-roadmap-contract.md` … `47-doctrine-time-map-branches.md` — per-task pins of the family half.
- `~/projects/skills/docs/context-tree.md` — the time-map doctrine the design extends (named roadmaps = branches of time; Features table = trunk).

## 3. Current state

**Done:**
- Governing spec `docs/multiuser-roadmaps.md` written, reviewed, committed in the skills repo (commit `6b6b2db` there).
- Skills-side work decomposed: Phase 4 with tasks 4.1–4.5 (engine resolution mechanism → writers → readers → prune policy → doctrine), specs 43–47 on disk, committed.

**In-flight:**
- Nothing in this repo. The skills-side tasks are queued for the orchestrator run there, not yet executed.

**Uncommitted working-tree state:**
- none (in this repo).

## 4. Next step
Add the roadmap-path setting and thread it to the existing `roadmap_filename` seam: the implement loop reads the roadmap file from the setting, default `.ai-factory/ROADMAP.md` (absence of the setting must be byte-equivalent to today); a named value points at `.ai-factory/roadmaps/<slug>.md`. Test mode derives the sibling of the roadmap in play — default → `ROADMAP_TESTS.md`, named → `.ai-factory/roadmaps/<slug>-tests.md` — never independently. Note `roadmap_filename` is today a *filename* joined under `.ai-factory/`; a named roadmap needs a *relative path* under `.ai-factory/` — widen the parameter's semantics accordingly. Everything else stays: artifact dirs flat, specs resolved via the contract line's `Spec:` tag (exact path — per-roadmap spec subdirectories are invisible to readers), sidecar and commit flows unchanged.

## 5. Working discipline
- Design forks are settled in dialogue fast: present options with one recommendation, confirm before structural decisions; the user reverses freely — treat the governing spec, not chat memory, as the settled state.
- **Never commit without explicit permission.** Selective staging on request is normal.
- "Defaults byte-stable" is a hard acceptance criterion, not a preference: a project with no `.ai-factory/roadmaps/` must see zero behavior change.

## 8. Domain model spine
- **Naming key is `git config user.email` local-part** (slugified: lowercase, non-alnum runs → one hyphen), NOT `user.name` — uniqueness and stability; don't re-litigate. Spec § «Имя файла».
- **Owner line** `> Owner: <full email>` is the loud collision stop for "my roadmap" resolution. The orchestrator takes an explicit path from its setting — explicit always wins, so the orchestrator performs no identity derivation; verifying the owner line before a run is optional hardening, not a requirement.
- **Specs of a named roadmap live in `.ai-factory/specs/<slug>/`** — settled after two reversals (flat-with-collisions and filename-prefixes both rejected); readers are unaffected because the `Spec:` tag always carries the exact path. Don't re-litigate. Spec § «Разрешение целевого файла».
- **Orchestrator artifact dirs stay flat** (`plans/`, `plan-reviews/`, `reviews/`, `patches/`, `test-runs/`) — branch-local, transient, swept by prune; explicitly carved out of the subdirectory split. Spec, same section.
- **Prune and the Features table are integration-branch operations** — one actor, after merges; the drop-history ledger is repo-wide (`git show <snapshot>:<roadmap path>` reconstructs any roadmap). No orchestrator involvement.
- **Cross-roadmap dependencies are developer discipline** (PR ordering), deliberately not a mechanism — documented decision, not a gap.

## 9. Hard rules
- Never commit without explicit permission.
- Generated artifacts in English regardless of conversation language.
- Lazy migration everywhere: named roadmaps are opt-in; the default layout is never touched.

## 10. Cross-cutting contracts / invariants checklist
- Named roadmap: `.ai-factory/roadmaps/<slug>.md`; test sibling: `.ai-factory/roadmaps/<slug>-tests.md`.
- Slug rule: `user.email` local-part, lowercase, every non-alphanumeric run → one hyphen (`kg.wmservice@gmail.com` → `kg-wmservice`); fallback slugified `user.name`.
- Owner line: `> Owner: <full email>` — exact form, first line of the file, written at creation.
- Resolution order (family-wide, identical wording everywhere): explicit argument → "my roadmap" → default `.ai-factory/ROADMAP.md`.
- One writer per roadmap file — the invariant the whole scheme rests on.
