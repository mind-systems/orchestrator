"""Unit tests for _has_signal, TestRunner._extract_test_command, and _resolve_claude."""

from pathlib import Path

import pytest

from orchestrator import agents
from orchestrator.agents import _has_signal, TestRunner


# ---------------------------------------------------------------------------
# Task 1: match within the last-5-line window
# ---------------------------------------------------------------------------


def test_signal_on_last_line():
    """Signal is the exact last line — most common case."""
    text = "some preamble\nmore text\nREVIEW_PASS"
    assert _has_signal(text, "REVIEW_PASS") is True


def test_signal_on_line_3_of_5():
    """Signal is on line 3 of 5: still inside the last-5 window."""
    lines = ["line1", "line2", "REVIEW_PASS", "line4", "line5"]
    assert _has_signal("\n".join(lines), "REVIEW_PASS") is True


def test_signal_on_line_6_of_10():
    """Signal is the first line inside the last-5 window of a 10-line text."""
    # Lines 1-5 (indices 0-4) are outside [-5:]; line 6 (index 5) is first inside.
    lines = [
        "line1", "line2", "line3", "line4", "line5",
        "REVIEW_PASS",  # index 5 — first line of [-5:]
        "line7", "line8", "line9", "line10",
    ]
    assert _has_signal("\n".join(lines), "REVIEW_PASS") is True


def test_signal_is_plan_review_pass():
    """Function is signal-agnostic: PLAN_REVIEW_PASS works the same way."""
    text = "planning notes\nPLAN_REVIEW_PASS"
    assert _has_signal(text, "PLAN_REVIEW_PASS") is True


# ---------------------------------------------------------------------------
# Task 2: window exclusion and exact-match rejection
# ---------------------------------------------------------------------------


def test_signal_on_line_5_of_10_excluded():
    """Signal is on line 5 (index 4) of a 10-line text — just outside [-5:]."""
    lines = [
        "line1", "line2", "line3", "line4",
        "REVIEW_PASS",  # index 4 — excluded by [-5:]
        "line6", "line7", "line8", "line9", "line10",
    ]
    assert _has_signal("\n".join(lines), "REVIEW_PASS") is False


def test_signal_as_substring_rejected():
    """Signal embedded in a longer line must NOT match (strip+equality check)."""
    text = "some text\nno REVIEW_PASS here\nmore text"
    assert _has_signal(text, "REVIEW_PASS") is False


def test_signal_with_surrounding_whitespace():
    """A line with leading/trailing whitespace still matches after strip()."""
    text = "preamble\n  REVIEW_PASS  \ntrailer"
    assert _has_signal(text, "REVIEW_PASS") is True


def test_empty_text_returns_false():
    """Empty string has no lines; any() over an empty iterable is False."""
    assert _has_signal("", "REVIEW_PASS") is False


# ---------------------------------------------------------------------------
# Task 1: backtick-wrapped command
# ---------------------------------------------------------------------------


def test_extract_test_command_backtick_wrapped(tmp_path):
    """Should return the command without backticks when the command line is wrapped in single backticks."""
    p = tmp_path / "plan.md"
    p.write_text("## Test Command\n`uv run pytest tests/ -v`")
    assert TestRunner._extract_test_command(p) == "uv run pytest tests/ -v"


# ---------------------------------------------------------------------------
# Task 2: bare command without backticks
# ---------------------------------------------------------------------------


def test_extract_test_command_bare(tmp_path):
    """Should return the command string as-is when the command line has no backticks."""
    p = tmp_path / "plan.md"
    p.write_text("## Test Command\nuv run pytest tests/ -v")
    assert TestRunner._extract_test_command(p) == "uv run pytest tests/ -v"


# ---------------------------------------------------------------------------
# Task 3: command after intervening blank lines
# ---------------------------------------------------------------------------


def test_extract_test_command_blank_lines(tmp_path):
    """Should return the first non-empty non-heading line when blank lines follow the heading."""
    p = tmp_path / "plan.md"
    p.write_text("## Test Command\n\n\nuv run pytest -v")
    assert TestRunner._extract_test_command(p) == "uv run pytest -v"


# ---------------------------------------------------------------------------
# Task 4: heading absent
# ---------------------------------------------------------------------------


def test_extract_test_command_no_heading(tmp_path):
    """Should return None when the plan has no Test Command heading."""
    p = tmp_path / "plan.md"
    p.write_text("# Some Plan\n## Other Section\nrun this")
    assert TestRunner._extract_test_command(p) is None


# ---------------------------------------------------------------------------
# Task 5: empty section before next heading
# ---------------------------------------------------------------------------


def test_extract_test_command_empty_section(tmp_path):
    """Should return None when the Test Command section is blank up to the next heading."""
    p = tmp_path / "plan.md"
    p.write_text("## Test Command\n\n## Next Section\nuv run pytest")
    assert TestRunner._extract_test_command(p) is None


# ---------------------------------------------------------------------------
# --- _resolve_claude ---
# ---------------------------------------------------------------------------


def _make_claude_bin(node_dir: Path) -> Path:
    """Create `node_dir/bin/claude` as an empty file and return its path.

    Content is irrelevant — `_resolve_claude` only calls `.exists()` on it.
    """
    bin_dir = node_dir / "bin"
    bin_dir.mkdir(parents=True)
    claude_bin = bin_dir / "claude"
    claude_bin.write_text("")
    return claude_bin


# ---------------------------------------------------------------------------
# Task 2: PATH-hit tests
# ---------------------------------------------------------------------------


def test_resolve_claude_path_hit(monkeypatch):
    """Returns the PATH-resolved path directly when shutil.which finds it."""
    monkeypatch.setattr(agents.shutil, "which", lambda name: "/usr/local/bin/claude")
    assert agents._resolve_claude() == "/usr/local/bin/claude"


def test_resolve_claude_path_hit_short_circuits_nvm(monkeypatch, tmp_path):
    """A PATH hit short-circuits the nvm fallback — no FileNotFoundError even
    though the patched home has no `.nvm` at all."""
    monkeypatch.setattr(agents.shutil, "which", lambda name: "/usr/local/bin/claude")
    monkeypatch.setattr(agents.Path, "home", lambda: tmp_path / "nonexistent_home")
    assert agents._resolve_claude() == "/usr/local/bin/claude"


# ---------------------------------------------------------------------------
# Task 3: not-found tests -> FileNotFoundError with install message
# ---------------------------------------------------------------------------


def test_resolve_claude_no_nvm_dir_raises(monkeypatch, tmp_path):
    """Raises when the fake home exists but has no `.nvm` inside it at all."""
    fakehome = tmp_path / "fakehome"
    fakehome.mkdir()
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    with pytest.raises(FileNotFoundError, match="npm install -g @anthropic-ai/claude-code"):
        agents._resolve_claude()


def test_resolve_claude_empty_node_versions_dir_raises(monkeypatch, tmp_path):
    """Raises when `.nvm/versions/node/` exists but is empty."""
    fakehome = tmp_path / "fakehome"
    (fakehome / ".nvm" / "versions" / "node").mkdir(parents=True)
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    with pytest.raises(FileNotFoundError, match="npm install -g @anthropic-ai/claude-code"):
        agents._resolve_claude()


def test_resolve_claude_no_bin_claude_in_any_version_raises(monkeypatch, tmp_path):
    """Raises when version dirs exist but none has a `bin/claude` file."""
    fakehome = tmp_path / "fakehome"
    node_dir = fakehome / ".nvm" / "versions" / "node"
    (node_dir / "v18.0.0").mkdir(parents=True)
    (node_dir / "v20.1.0").mkdir(parents=True)
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    with pytest.raises(FileNotFoundError, match="npm install -g @anthropic-ai/claude-code"):
        agents._resolve_claude()


# ---------------------------------------------------------------------------
# Task 4: nvm candidate selection -- multi-candidate, partial-install,
# non-dir tolerance
# ---------------------------------------------------------------------------


def test_resolve_claude_multi_candidate_returns_highest(monkeypatch, tmp_path):
    """When multiple version dirs each have `bin/claude`, and the sort happens
    to agree with semver order, the highest-sorting one is returned."""
    fakehome = tmp_path / "fakehome"
    node_dir = fakehome / ".nvm" / "versions" / "node"
    _make_claude_bin(node_dir / "v18.0.0")
    v20 = _make_claude_bin(node_dir / "v20.1.0")
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    assert agents._resolve_claude() == str(v20)


def test_resolve_claude_partial_install_skipped(monkeypatch, tmp_path):
    """A version dir with no `bin/claude` is skipped in favor of the next
    candidate that has one, with no raise."""
    fakehome = tmp_path / "fakehome"
    node_dir = fakehome / ".nvm" / "versions" / "node"
    (node_dir / "v20.1.0").mkdir(parents=True)
    v18 = _make_claude_bin(node_dir / "v18.0.0")
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    assert agents._resolve_claude() == str(v18)


def test_resolve_claude_non_dir_entry_tolerated(monkeypatch, tmp_path):
    """A stray non-version entry (unparseable name, sorts last) is
    tolerated without a crash, and the valid version dir is still
    returned."""
    fakehome = tmp_path / "fakehome"
    node_dir = fakehome / ".nvm" / "versions" / "node"
    node_dir.mkdir(parents=True)
    (node_dir / "zzstray").write_text("")  # unparseable name, sorts last / is skipped
    v18 = _make_claude_bin(node_dir / "v18.0.0")
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    assert agents._resolve_claude() == str(v18)


# ---------------------------------------------------------------------------
# Task 5: RED case -- semver ordering (fixed in milestone 2.2)
# ---------------------------------------------------------------------------


def test_resolve_claude_semver_ordering_picks_true_latest(monkeypatch, tmp_path):
    """The true-latest version (v20.11.0) should win over v9.0.0. Today's
    `sorted(..., reverse=True)` compares directory names lexicographically,
    so it picks v9.0.0 instead -- this assertion encodes the correct
    behavior and is expected to fail until the sort is semver-aware."""
    fakehome = tmp_path / "fakehome"
    node_dir = fakehome / ".nvm" / "versions" / "node"
    _make_claude_bin(node_dir / "v9.0.0")
    v20 = _make_claude_bin(node_dir / "v20.11.0")
    monkeypatch.setattr(agents.shutil, "which", lambda name: None)
    monkeypatch.setattr(agents.Path, "home", lambda: fakehome)
    assert agents._resolve_claude() == str(v20)


# ---------------------------------------------------------------------------
# Task 2: _sorted_nvm_node_dirs -- direct unit cases on the pure helper
# ---------------------------------------------------------------------------


def test_sorted_nvm_node_dirs_orders_by_semver_not_lexicographic():
    """Single- vs double-digit majors order semantically: v20 and v10 both
    outrank v9, which a plain lexicographic sort would get wrong."""
    dirs = [Path("v9.0.0"), Path("v20.11.0"), Path("v10.0.0")]
    result = agents._sorted_nvm_node_dirs(dirs)
    assert [d.name for d in result] == ["v20.11.0", "v10.0.0", "v9.0.0"]


def test_sorted_nvm_node_dirs_unparseable_sorts_last():
    """Unparseable names (no leading decimal segment) sort after every
    parseable version, ordered among themselves by string name."""
    dirs = [Path("v18.20.4"), Path("system"), Path("v20.1.0")]
    result = agents._sorted_nvm_node_dirs(dirs)
    assert [d.name for d in result] == ["v20.1.0", "v18.20.4", "system"]


def test_sorted_nvm_node_dirs_empty_list_never_raises():
    """An empty input list returns an empty list without raising."""
    assert agents._sorted_nvm_node_dirs([]) == []
