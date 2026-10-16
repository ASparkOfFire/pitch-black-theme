"""Check every Pitch Black variant for readability problems on pure black.

Exits non-zero if any variant has an issue.

    python3 scripts/audit.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import THEME_FILE, contrast, delta_e  # noqa: E402

# Keys Zed fills from its default theme with visible grey/blue when unset.
REQUIRED = [
    "tab.active_background", "search.active_match_background", "element.selection_background",
    "panel.overlay_background", "panel.overlay_hover", "editor.debugger_active_line.background",
    "editor.hover_line_number", "scrollbar.thumb.active_background", "drop_target.border",
    "version_control.word_added", "version_control.word_deleted",
    "version_control.conflict_marker.ours", "version_control.conflict_marker.theirs",
    "editor.diff_hunk.added.hollow_background", "editor.diff_hunk.deleted.hollow_background",
]
ANSI = ("red", "green", "yellow", "blue", "magenta", "cyan")


def audit(s):
    issues = []
    sel = s["players"][0]["selection"]
    missing = [k for k in REQUIRED if k not in s]
    if missing:
        issues.append(f"unset (falls back to Zed default): {', '.join(missing)}")
    if contrast(s["tab.active_background"], s["tab.inactive_background"]) < 1.2:
        issues.append("active tab indistinguishable from inactive tabs")
    for key, minimum in (("text", 7), ("text.muted", 4.5), ("editor.line_number", 3)):
        if contrast(s[key]) < minimum:
            issues.append(f"{key} {s[key]} only {contrast(s[key]):.1f}:1")
    if contrast(sel) < 1.4:
        issues.append(f"selection {sel} barely visible")
    if delta_e(s["search.match_background"], sel) < 15:
        issues.append("search matches look like the selection")
    active = s.get("search.active_match_background")
    if active and contrast(s["text"], active) < 3:
        issues.append("text unreadable on the active search match")
    for kind in ("added", "deleted"):
        if contrast(s[f"editor.diff_hunk.{kind}.background"]) < 1.25:
            issues.append(f"{kind} diff lines faint")
    same = [a for a in ANSI if s[f"terminal.ansi.{a}"] == s[f"terminal.ansi.bright_{a}"]]
    if same:
        issues.append(f"terminal bright == normal for {', '.join(same)}")
    r, g, b = (int(s["terminal.ansi.bright_black"][i:i + 2], 16) for i in (1, 3, 5))
    if max(r, g, b) - min(r, g, b) > 90:
        issues.append(f"terminal bright_black is saturated ({s['terminal.ansi.bright_black']})")
    for label, colors in (("players", [p["cursor"] for p in s["players"]]), ("accents", s["accents"])):
        dupes = sum(1 for i, c in enumerate(colors) if any(delta_e(c, o) < 12 for o in colors[:i]))
        if dupes:
            issues.append(f"{label}: {dupes} near-duplicate colour(s)")
    for a, b in (("created", "renamed"), ("created", "deleted"), ("modified", "deleted")):
        if delta_e(s[a], s[b]) < 15:
            issues.append(f"git {a} and {b} look alike")
    return issues


def main():
    themes = json.loads(THEME_FILE.read_text())["themes"]
    failed = 0
    for theme in themes:
        issues = audit(theme["style"])
        if issues:
            failed += 1
            print(f"{theme['name']}:")
            print("\n".join(f"  - {i}" for i in issues))
    print(f"{len(themes) - failed}/{len(themes)} variants clean")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
