"""Parse and update .ai-factory/ROADMAP.md files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CHECKBOX_RE = re.compile(r"^- \[([ x])\] \*\*(.+?)\*\*\s*[—–-]\s*(.+)$")


@dataclass
class Milestone:
    title: str
    description: str
    done: bool
    line_number: int  # 0-based line index in file
    section: str | None = None

    @property
    def slug(self) -> str:
        """Convert title to a filename-safe slug."""
        s = self.title.lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        return s.strip("-")


@dataclass
class ParseResult:
    milestones: list[Milestone]
    breakpoint_hit: bool
    milestones_after_breakpoint: int


def parse_roadmap(path: Path) -> ParseResult:
    """Parse ROADMAP.md and return ParseResult.

    When a ``---STOP---`` marker is present and at least one milestone follows it,
    only milestones before the marker are returned and ``breakpoint_hit`` is True.
    A marker with nothing after it is treated as if it weren't there.
    """
    lines = path.read_text().splitlines()
    milestones: list[Milestone] = []
    marker_found = False
    milestones_after_breakpoint = 0
    current_section: str | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            current_section = stripped.lstrip("#").strip()

        if marker_found:
            if CHECKBOX_RE.match(stripped):
                milestones_after_breakpoint += 1
            continue

        if stripped == "---STOP---":
            marker_found = True
            continue

        m = CHECKBOX_RE.match(stripped)
        if m:
            done = m.group(1) == "x"
            title = m.group(2).strip()
            description = m.group(3).strip()
            milestones.append(Milestone(title=title, description=description, done=done, line_number=i, section=current_section))

    breakpoint_hit = marker_found and milestones_after_breakpoint > 0
    return ParseResult(milestones=milestones, breakpoint_hit=breakpoint_hit, milestones_after_breakpoint=milestones_after_breakpoint)


def mark_done(path: Path, milestone: Milestone, elapsed_secs: int | None = None) -> None:
    """Mark a milestone as completed in ROADMAP.md."""
    lines = path.read_text().splitlines()
    line = lines[milestone.line_number]
    new_line = line.replace("- [ ]", "- [x]", 1)
    if elapsed_secs is not None:
        mins, secs = divmod(elapsed_secs, 60)
        hours, mins = divmod(mins, 60)
        time_str = f"{hours}h {mins}m {secs}s" if hours else f"{mins}m {secs}s"
        new_line = new_line.rstrip() + f" [{time_str}]"
    lines[milestone.line_number] = new_line
    path.write_text("\n".join(lines) + "\n")


def mark_skipped(path: Path, milestone: Milestone) -> None:
    """Mark a milestone as skipped (already done) in ROADMAP.md."""
    lines = path.read_text().splitlines()
    line = lines[milestone.line_number]
    lines[milestone.line_number] = line.replace("- [ ]", "- [x] ⚠️ SKIPPED (already implemented)", 1)
    path.write_text("\n".join(lines) + "\n")
