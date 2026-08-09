# Settings as a modal in the same application

**Date:** 2026-08-09
**Source:** conversation context (Phase 22, `docs/future/operator-surface.md` § "Settings live where runs start"); absorbs the reusable half of the now-deleted REPL exploration

## Problem today

Configuration is a file, hand-edited, read once at process startup (`load_config`, `config.py`). Changing `max_iterations` or any other threshold between runs means leaving the application, editing `orchestrator.json` (or its per-project overlay), and starting again — there is no in-application way to read or change a setting.

## The change

A modal screen inside 22.1's shell, opened by its own key binding, showing the current values of the same four fields the abandoned REPL spec validated (`max_iterations`, `usage_threshold_5h`, `usage_threshold_weekly`, `enable_phase_sessions`), editable in place. Closing the modal with a save applies the changes to the next run started from the application; closing without saving discards them.

**Absorbed from the abandoned REPL spec, verbatim in behavior:**

- Per-field type validation:
  ```python
  FIELD_TYPES = {
      "max_iterations": int,
      "usage_threshold_5h": float,
      "usage_threshold_weekly": float,
      "enable_phase_sessions": lambda v: v.lower() not in ("false", "0", "no"),
  }
  ```
  `enable_phase_sessions` accepts `true/false`, `1/0`, `yes/no`, case-insensitive.
- Atomic write: `config_path.with_suffix(".json.tmp")`, write, `os.replace(tmp, config_path)` — the same tmp-then-replace pattern `_write_session` already uses elsewhere in this codebase.
- Guards: an unknown key is a named, non-crashing error; an invalid value for a known key's type is a named, non-crashing error.

**Not absorbed:** the line-prompt shape (`> ` input loop, its command-parsing dispatch) and the `implement`/`test`/`show`/`help`/`exit` command surface — Phase 22's shell already provides navigation and run-starting through the tree and `i`/`t` (22.1/22.3), so none of that dispatch logic is needed. Also not absorbed: the abandoned spec's mention of translating an outcome into an exit status of `0`, `75`, or a re-raise — no such status exists in this design; this task carries no exit-status behavior at all.

## Guards

- The modal edits a working copy; nothing is written to disk until an explicit save action, matching the abandoned spec's `save`/`set` separation (mutate in memory, persist on demand).
- The four validated fields and their types are exactly the four above — no new setting is added by this task.
- The save path is the same `config_path` the shell's own config was loaded from — never a hardcoded path.
- A change applies only to the next run started from the application after the save — a run already in flight (22.3) is unaffected.

## Tests

`tests/test_config.py` or wherever `FIELD_TYPES`-equivalent validation logic lands (matching whichever module hosts it):

- Each of the four fields accepts a valid value of its type and rejects an invalid one with a named error, not a crash.
- `enable_phase_sessions` accepts `true/false/1/0/yes/no` case-insensitively.
- An unknown key produces a named error.
- The save path performs a tmp-write then `os.replace`, and the resulting file round-trips through `load_config`.

## Verify

- `uv run pytest` green, including the validation and atomic-write cases.
- Manual trace: opening the modal, changing `max_iterations`, saving, then starting a run from the shell uses the new value; closing without saving leaves the on-disk file untouched.

## What NOT to do

- Do not resurrect the line-prompt input loop or its command dispatch.
- Do not add a fifth configurable field.
- Do not reference exit-status behavior of any kind.
- Touch the shell module's new settings-modal screen and its validation/write helpers only.
