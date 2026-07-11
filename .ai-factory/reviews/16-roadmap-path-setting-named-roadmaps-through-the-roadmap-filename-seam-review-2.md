# Re-review: Roadmap-path setting — named roadmaps through the `roadmap_filename` seam (attempt 2)

Re-read every cited file fresh (not from session memory), re-ran the full suite (`110 passed`), and re-scanned the whole change set (`git diff HEAD`) for new issues. The only code delta since attempt 1 is the owner-line fix plus one added regression test.

## Prior findings

### 1. Owner-line gate broken when identity derives from `git user.name` (no `user.email`) — always HaltError → **Fixed**

`main.py:143-151` (current content):

```python
lines = roadmap_file.read_text().splitlines()
first_line = lines[0] if lines else ""
identity = email or name
expected_owner = f"> Owner: {identity}"
if first_line.strip() != expected_owner:
    raise HaltError(
        f"Named roadmap {relpath} owner line ({first_line!r}) does not match "
        f"the current git identity ({expected_owner!r})."
    )
```

The interpolated token changed from the raw `email` (which was `None` on the name-fallback path) to `identity = email or name`, matching the precedence `_derive_identity_slug` itself uses (email first, then name). When git email is unset but a name is present, the expected line is now `> Owner: <name>` instead of the old nonsensical `> Owner: None`, so a correctly-owned, name-derived roadmap resolves instead of halting.

Evidence it exercises the fixed path — new test `test_resolve_roadmap_relpath_my_name_derived_owner_matches` (`tests/test_main.py:876-884`): git email `None`, name `Alice`, file `roadmaps/alice.md` starting `> Owner: Alice` → asserts the result is `"roadmaps/alice.md"`. This assertion fails under the old `f"> Owner: {email}"` code and passes now. Full suite green (110 passed).

## New review (full pass)

Re-read `orchestrator/config.py`, `orchestrator/main.py`, `orchestrator/prompts/reviewer.md`, `tests/test_config.py`, `tests/test_main.py`, `docs/configuration.md`, `docs/target-project.md` in full. No new correctness, security, or runtime findings:

- Three-state resolution is disjoint and matches the spec; byte-stable default preserved (`config.roadmap_path is None → "ROADMAP.md"`).
- Config guard rejects absolute paths and any `..` segment before construction; `grep` confirms zero `roadmap_filename` references remain after the rename.
- `_tests_sibling` special-cases the default pair and derives `-tests` siblings for named/nested paths via `pathlib`.
- `_test_loop` / `_implement_loop` wiring resolves the relpath once and threads it through `Mode._replace`; generalized missing-file messages are correct.
- `reviewer.md` widenings are wording-only and preserve the skip-if-no-match tail.
- Tests and docs cover the new surfaces; the git-config reads are stubbed, never hitting the real environment.

(Non-blocking, unchanged from attempt 1 and intended per spec: in `test` mode `_resolve_roadmap_relpath` resolves and owner-checks the *main* roadmap before the `-tests` sibling is derived — a documented consequence of "the sibling is always derived from the roadmap in play." No change requested.)

REVIEW_PASS
