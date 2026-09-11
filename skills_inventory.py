"""Inventory of installed Claude skills -> skills-installed.json.

Run locally after installing or removing skills; the skills edition excludes
anything listed here. Scans the user skill dir, plugins, and Anthropic's
bundled skills so nothing already available gets recommended.
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent
HOME = Path.home()
ROOTS = [
    HOME / ".claude" / "skills",
    HOME / ".claude" / "plugins",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "claude" / "bundled-skills",
]


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    fm = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


skills = {}
for root in ROOTS:
    if not root.exists():
        continue
    for p in root.rglob("SKILL.md"):
        fm = frontmatter(p)
        name = fm.get("name") or p.parent.name
        skills.setdefault(name, {"name": name, "description": fm.get("description", "")[:160],
                                 "source": root.name})

out = sorted(skills.values(), key=lambda s: s["name"])
(ROOT / "skills-installed.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(f"{len(out)} installed skills -> skills-installed.json")
