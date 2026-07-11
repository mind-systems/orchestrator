# Review: Roadmap-path setting — named roadmaps through the `roadmap_filename` seam (attempt 1)

Scope reviewed: `orchestrator/config.py`, `orchestrator/main.py`, `orchestrator/prompts/reviewer.md`, `tests/test_config.py`, `tests/test_main.py`, `docs/configuration.md`, `docs/target-project.md`. Full `git diff HEAD` read; each changed file read in full and cross-checked against spec `.ai-factory/specs/12-roadmap-path-setting.md`. Full test suite passes (`65 passed`).

The implementation is faithful to the spec on all core paths: three-state resolution, the `..`/absolute config guard, the `roadmap_filename → roadmap_relpath` rename (grep confirms zero `roadmap_filename` hits remain), the `_tests_sibling` special-casing of the default pair, the test-sibling derivation, and the two `reviewer.md` widenings. Byte-stable default is preserved (`config.roadmap_path is None → "ROADMAP.md"`). One correctness finding and one lower-severity note follow.

## Findings

### 1. Owner-line gate is broken when identity derives from `git user.name` (no `user.email`) — always HaltError

`main.py` `_resolve_roadmap_relpath`:

```python
slug = _derive_identity_slug(email, name)   # may derive from `name` when email is None
...
expected_owner = f"> Owner: {email}"        # email is still None here
if first_line.strip() != expected_owner:
    raise HaltError(...)
```

`_derive_identity_slug` deliberately falls back to slugifying `name` when `email` is empty/None (that fallback is spec'd and unit-tested). But the owner check then interpolates `email` directly into the expected line. When email is `None` and the slug came from the name, `expected_owner` becomes the literal string `"> Owner: None"`, which can never match a real owner line — so the `"my"` path **always raises `HaltError`** for a name-derived identity, even against a correctly-owned roadmap.

Reproduced live: git `user.email` unset, `user.name = Alice`, `.ai-factory/roadmaps/alice.md` starting `> Owner: Alice` →
`HaltError -> Named roadmap roadmaps/alice.md owner line ('> Owner: Alice') does not match the current git identity ('> Owner: None').`

Failure scenario: any workstation with a git name but no git email set, `roadmap_path: "my"`, and its named roadmap present — the run halts on every invocation instead of running the queue. The name-fallback branch of `_derive_identity_slug` (which exists precisely for the no-email case) is therefore unreachable in practice for the owner gate.

The spec (step 1/2) phrases the owner line as `> Owner: <email>` and does not pin the format when only a name is available, so the exact fix is a judgment call — either derive the identity token once (`identity = email or name`) and compare `f"> Owner: {identity}"`, or skip the owner check when email is absent. Either way, `f"> Owner: {email}"` with a possibly-`None` `email` is a latent bug: it emits a nonsensical `"> Owner: None"` and a confusing halt message. Confirmed by code + live repro.

## Notes (non-blocking)

- **Test-mode resolves and owner-checks the *main* roadmap, not the test sibling.** `_test_loop` calls `_resolve_roadmap_relpath` (which, for `"my"`, verifies the main `roadmaps/<slug>.md` owner line and falls back to `ROADMAP.md` when the main file is missing), then derives the `-tests` sibling from the result. This matches the spec ("the sibling is always derived from the roadmap in play, never configured independently … including `"my"` and its fallback"), so it is intended behavior — flagged only so the coupling is visible: a `test` run can halt on the *main* roadmap's owner mismatch, and a present `roadmaps/<slug>-tests.md` is ignored when the main `roadmaps/<slug>.md` is absent (fallback lands on `ROADMAP_TESTS.md`). No change requested.

Because finding 1 is a real correctness defect on the name-fallback path, this review does not pass.
