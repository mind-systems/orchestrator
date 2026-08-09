# Architect buffer

Deliberately deferred work. Each entry: what, why it is not being done now, and the trigger that resolves it. An entry is deleted once it is done — this file holds only what is still open.

## `docs/future/run-context-refactor.md` has drifted

**What.** The doc is in Russian while the rest of the tree is English, and it names `milestones_done` and `process_milestone` — vocabulary the code dropped; it is `tasks_done` now. Its premise also moved twice in one session: it briefly became a precondition for holding several runs in one process, then returned to a readability improvement when runs became child processes instead.

**Why deferred.** Nothing depends on it. It describes a refactor that is not queued, and correcting it now buys nothing.

**Trigger.** Any sweep over `docs/`, or a decision that would put runs back inside one process — at which point the doc stops being optional and becomes a precondition again.
