"""Static status hub for the digest editions.

Derives everything from repo state — EDITIONS in digest.py, cron + recipients
from the workflow files, send history from the seen files — and writes
docs/index.html. Run by each digest workflow after a send; new editions that
follow the digest-{key}.yml convention appear automatically.
"""

import html
import json
import re
from datetime import date
from pathlib import Path

from digest import EDITIONS, LOGO_URL, MODEL

ROOT = Path(__file__).parent

DAYS = {"0": "Sundays", "1": "Mondays", "2": "Tuesdays", "3": "Wednesdays",
        "4": "Thursdays", "5": "Fridays", "6": "Saturdays", "7": "Sundays"}

# Shown on the hub instead of raw addresses (the page may be public).
NAMES = {
    "rowan.flynn@wausaupilotandreview.com": "Rowan Flynn",
    "editor@wausaupilotandreview.com": "Shereen (editor)",
}


def workflow_path(key: str) -> Path:
    name = "digest.yml" if key == "wpr" else f"digest-{key}.yml"
    return ROOT / ".github" / "workflows" / name


def parse_workflow(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    cron = re.search(r'cron:\s*"([^"]+)"', text).group(1)
    to = re.search(r"DIGEST_TO:\s*(.+)", text).group(1)
    return cron, [a.strip() for a in to.split(",")]


def build() -> str:
    e = html.escape
    serif = "Georgia,'Times New Roman',serif"
    sans = "'Helvetica Neue',Helvetica,Arial,sans-serif"

    cards, total_items = [], 0
    for key, ed in EDITIONS.items():
        cron, recipients = parse_workflow(workflow_path(key))
        minute, hour, dom, _, dow = cron.split()
        if dow in DAYS:
            day = DAYS[dow]
        elif dom != "*":
            suffix = {"1": "st", "2": "nd", "3": "rd"}.get(dom, "th")
            day = f"{dom}{suffix} of each month"
        else:
            day = "Daily"
        h = (int(hour) - 5) % 24  # UTC -> Central Daylight; an hour earlier in winter
        when = f"{h % 12 or 12}:{int(minute):02d} {'a.m.' if h < 12 else 'p.m.'} Central"
        seen = json.loads((ROOT / ed["seen"]).read_text(encoding="utf-8"))
        total_items += len(seen)
        last_sent = max((s["date"] for s in seen), default=None)
        who = ", ".join(NAMES.get(r, r.split("@")[0] + "@…") for r in recipients)
        recent = "".join(
            f'<li><a href="{e(s["url"])}">{e(s["name"])}</a>'
            f'<span class="d"> · {e(s["date"])}</span></li>'
            for s in reversed(seen[-4:])
        ) or "<li class='d'>nothing sent yet</li>"
        cards.append(f"""
    <section class="card" style="border-top-color:{ed['accent']}">
      <div class="kicker" style="color:{ed['accent']}">{e(day)} · {e(when)} · ${ed['max_cost']:.0f} cost cap</div>
      <h2>{e(ed['title'])}</h2>
      <div class="meta">
        <div><span class="label">To</span> {e(who)}</div>
        <div><span class="label">Last sent</span> {e(last_sent) if last_sent else "—"}</div>
        <div><span class="label">Items covered</span> {len(seen)}</div>
        <div><span class="label">Context file</span> <code>{e(ed['context'])}</code></div>
      </div>
      <div class="label" style="margin-top:14px">Most recent finds</div>
      <ul class="recent">{recent}</ul>
    </section>""")

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WPR Digest Hub</title>
<style>
  body {{ margin:0; background:#FFFFFF; color:#121212; font:16px/1.6 {serif}; }}
  .wrap {{ max-width:680px; margin:0 auto; padding:36px 20px 40px; }}
  header {{ text-align:center; padding-bottom:20px; border-bottom:3px solid #121212; }}
  header img {{ width:72px; height:72px; }}
  h1 {{ margin:10px 0 6px; font:700 34px/1.1 {serif}; }}
  .sub {{ font:600 11px/1.5 {sans}; color:#727272; letter-spacing:.14em; text-transform:uppercase; }}
  .card {{ margin:26px 0 0; padding:20px 22px; border:1px solid #E2E2E2; border-top:3px solid #121212; }}
  .kicker {{ font:700 11px/1.4 {sans}; letter-spacing:.12em; text-transform:uppercase; margin-bottom:8px; }}
  h2 {{ margin:0 0 12px; font:700 24px/1.2 {serif}; }}
  .meta {{ display:grid; grid-template-columns:1fr 1fr; gap:6px 18px; font-size:15px; }}
  .label {{ font:700 10px/1.6 {sans}; color:#8A8A8A; letter-spacing:.12em; text-transform:uppercase; display:block; }}
  code {{ font-size:13px; background:#F4F4F4; padding:1px 5px; }}
  .recent {{ margin:6px 0 0; padding-left:20px; font-size:15px; }}
  .recent li {{ margin:0 0 6px; }}
  .recent a {{ color:#121212; }}
  .d {{ color:#8A8A8A; font-size:13px; }}
  footer {{ margin-top:30px; padding-top:14px; border-top:1px solid #E2E2E2; text-align:center;
           font:12px/1.7 {sans}; color:#8A8A8A; }}
  @media (max-width:520px) {{ .meta {{ grid-template-columns:1fr; }} }}
</style>
</head><body>
<div class="wrap">
  <header>
    <img src="{LOGO_URL}" alt="Wausau Pilot &amp; Review">
    <h1>Digest Hub</h1>
    <div class="sub">{len(EDITIONS)} automated emails · {total_items} items covered · research by {e(MODEL)}</div>
  </header>
  {"".join(cards)}
  <footer>
    Regenerated after every send · {date.today():%B %d, %Y} ·
    <a href="https://github.com/RowanFlynnPilot/wpr-ai-digest" style="color:#8A8A8A">wpr-ai-digest</a>
  </footer>
</div>
</body></html>"""


if __name__ == "__main__":
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out}")
