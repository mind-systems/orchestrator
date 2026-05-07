# Code Review: Fix seq mismatch in resume detection

## Critical Issues

### 1. Slug glob matches false positives (suffix collision)

`main.py:94` — The glob `*-{slug}.md` matches files where the target slug is a suffix of a longer slug, because `*` absorbs both the numeric prefix and extra slug segments.

Example: milestone slug `fix-a`, existing file `14-also-fix-a.md`. The glob `*-fix-a.md` matches `14-also-fix-a.md`. The code would extract seq=14 and point `plan_path` at the wrong plan file.

The candidate loop at lines 98-104 must verify that the slug portion matches exactly:

```python
for f in slug_matches:
    parts = f.stem.split("-", 1)
    if parts[0].isdigit() and parts[1] == slug:
```

Without this guard, a seq mismatch fix can silently hijack the wrong milestone's plan.

REVIEW_PASS
