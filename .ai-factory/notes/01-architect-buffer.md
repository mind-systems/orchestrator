# Architect buffer

## Editor handle

- `a2e072d9ff36712d1` — agent type `editor`, spawned this session. Message it with `SendMessage`; never respawn while it answers.

## Pairing role

_None assigned._

## Deferred work

Deliberately deferred work. Each entry: what, why it is not being done now, and the trigger that resolves it. An entry is deleted once it is done — this file holds only what is still open.

- **A task spec's paths must resolve from the run's own working directory.** Every agent is launched with `cwd = project_dir` (`agents.py:427,472,524,576`), so a path written root-relative from the family root — `skills/src/...` — resolves to nothing during a run, and `docs/concepts/context-model.md:35` already commits to the contract line being the only guaranteed entry point. *Why deferred:* the one task that broke this has been deleted, so nothing is currently wrong; the rule has no home yet, and its likely home is the skills-side decomposition discipline, not this repo. *Trigger:* the next roadmap task here whose spec names a path outside this repository, or any session working on decomposition rules on the skills side.
