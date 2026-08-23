"""Weekly AI tools digest for WPR.

research() -> render() -> send(), then record what was covered so next week skips it.
"""

import html
import json
import os
import re
import smtplib
import sys
import urllib.request
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import urlparse

import anthropic

ROOT = Path(__file__).parent

EDITIONS = {
    "wpr": {"context": "context.md", "seen": "seen.json",
            "title": "AI Digest", "subject": "WPR AI Digest", "max_cost": 3.00,
            "accent": "#2E6B63"},
    "industry": {"context": "context-industry.md", "seen": "seen-industry.json",
                 "title": "AI in Local News", "subject": "AI in Local News", "max_cost": 3.00,
                 "accent": "#8C4425"},
    "tools": {"context": "context-tools.md", "seen": "seen-tools.json",
              "title": "AI Tools Radar", "subject": "AI Tools Radar", "max_cost": 4.00,
              "accent": "#44477F"},
}

MODEL = "claude-opus-5"
MAX_SEARCHES = 20
MAX_FETCHES = 12
FETCH_CONTENT_TOKENS = 10_000
MIN_ITEMS, MAX_ITEMS = 3, 10

# claude-opus-5 pricing ($/MTok) plus $10 per 1k web searches — keep in sync with MODEL
IN_RATE, OUT_RATE = 5.00, 25.00
CACHE_WRITE_RATE, CACHE_READ_RATE = 6.25, 0.50
SEARCH_COST = 0.01
MAX_ROUNDS = 10

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587

LOGO_URL = "https://wausaupilotandreview.com/wp-content/uploads/2024/04/cropped-Wausau-Pilot-Transparent-192x192.png"


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_prompt(context: str, seen: list[dict]) -> str:
    already = "\n".join(f"- {s['name']}" for s in seen) or "- (none yet)"
    return f"""{context}

# Already covered in previous digests (do not repeat)
{already}

# Task

Today is {date.today():%A, %B %d, %Y}. Search the web for AI tools, models, APIs, and product features
announced or materially updated in the last 10 days. Use several distinct searches across the categories
under "Worth surfacing" — do not stop after one or two queries. Prefer primary sources (vendor blogs,
GitHub releases, docs, changelogs) and journalism-sector outlets over aggregators. Before writing a
pitch, fetch the primary source page for each item you select to confirm the announcement date, the
actual capabilities, and pricing — the url field must be the primary source you fetched, never an
aggregator or search snippet.

Aim for 5–{MAX_ITEMS} finds when the week genuinely supports it — never pad with weak items to hit a
count, and never return fewer than {MIN_ITEMS}. Rank the items and write the pitch and applications
exactly as the "How to rank and pitch" section above directs — no generic "could help with content".

Respond with ONLY a raw JSON object: no prose before or after, no markdown code fences,
and no <cite> tags or any citation markup inside the values — plain text only:

{{
  "items": [
    {{
      "name": "Tool or feature name",
      "url": "https://primary-source-link",
      "what": "What it is, in one plain sentence (max 20 words)",
      "pitch": "Why it matters for WPR specifically (max 40 words)",
      "applications": ["Concrete use naming a WPR build or workflow (max 30 words)", "optional second use"],
      "access": "free | paid | open-source | waitlist (plus price if known, a few words)"
    }}
  ]
}}"""


def research(client: anthropic.Anthropic, context: str, seen: list[dict], max_cost: float) -> list[dict]:
    messages = [{"role": "user", "content": build_prompt(context, seen)}]
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": MAX_SEARCHES},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": MAX_FETCHES,
         "max_content_tokens": FETCH_CONTENT_TOKENS},
    ]

    # pause_turn continuations resend the whole growing conversation; cache_control
    # makes each round re-read the prior prefix at 10% of input price instead of full.
    # Cost is summed across every round — the final response's usage alone under-reports.
    cost, searches, fetches, rounds = 0.0, 0, 0, 0
    while True:
        rounds += 1
        if rounds > MAX_ROUNDS:
            raise RuntimeError(f"Exceeded {MAX_ROUNDS} continuation rounds — aborting")
        # Streaming keeps the connection alive however long the turn takes;
        # a non-streaming request hits the SDK's 10-minute timeout on long Opus turns.
        with client.messages.stream(
            model=MODEL, max_tokens=16000, messages=messages, tools=tools,
            cache_control={"type": "ephemeral"},
        ) as stream:
            response = stream.get_final_message()
        u, st = response.usage, response.usage.server_tool_use
        round_searches = st.web_search_requests if st else 0
        searches += round_searches
        fetches += (getattr(st, "web_fetch_requests", 0) or 0) if st else 0
        cost += round_searches * SEARCH_COST + (
            u.input_tokens * IN_RATE
            + (u.cache_creation_input_tokens or 0) * CACHE_WRITE_RATE
            + (u.cache_read_input_tokens or 0) * CACHE_READ_RATE
            + u.output_tokens * OUT_RATE
        ) / 1e6
        if cost > max_cost:
            raise RuntimeError(f"Run cost ${cost:.2f} exceeded the ${max_cost:.2f} cap — aborting")
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        if response.stop_reason != "end_turn":
            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")
        break

    print(f"model={MODEL} searches={searches} fetches={fetches} cost=${cost:.2f}")

    # Citations from web search split the final answer across many text blocks;
    # the answer is everything after the last tool block, joined back together.
    non_text = [i for i, block in enumerate(response.content) if block.type != "text"]
    answer = "".join(block.text for block in response.content[(non_text[-1] + 1) if non_text else 0:]).strip()
    if not answer:
        raise RuntimeError("No answer text after the final search block")
    if answer.startswith("```"):
        answer = answer.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    answer = re.sub(r"</?cite[^>]*>", "", answer)
    try:
        items = json.loads(answer)["items"]
    except json.JSONDecodeError as err:
        raise RuntimeError(f"Model did not return JSON. Answer began: {answer[:300]!r}") from err
    if not MIN_ITEMS <= len(items) <= MAX_ITEMS:
        raise RuntimeError(f"Expected {MIN_ITEMS}–{MAX_ITEMS} items, got {len(items)}")
    return items


def fetch_og_image(url: str) -> str | None:
    """Best-effort og:image lookup. Decorative only — never fails the run."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; wpr-ai-digest)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            head = r.read(300_000).decode("utf-8", "replace")
    except Exception:
        return None
    m = (re.search(r'<meta[^>]+property=["\']og:image["\'][^>]*content=["\']([^"\']+)', head)
         or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', head))
    if m and m.group(1).startswith("http"):
        return html.unescape(m.group(1))
    return None


def render(items: list[dict], today: date, edition: dict) -> str:
    e = html.escape
    accent = edition["accent"]
    sans = "'Libre Franklin','Helvetica Neue',Helvetica,Arial,sans-serif"
    serif = "Georgia,'Times New Roman',serif"

    blocks = []
    for i, item in enumerate(items, 1):
        apps = "".join(f'<li style="margin:0 0 7px;">{e(a)}</li>' for a in item["applications"])
        domain = urlparse(item["url"]).netloc.removeprefix("www.")
        image = ""
        if item.get("image"):
            image = f"""
    <a href="{e(item["url"])}" style="text-decoration:none;">
      <img src="{e(item["image"])}" width="600" alt=""
           style="display:block;width:100%;max-width:600px;height:auto;margin:0 0 14px;border:1px solid #EBEBEB;"></a>"""
        blocks.append(f"""
  <div style="padding:28px 0;border-bottom:1px solid #E2E2E2;">
    <div style="margin:0 0 10px;font:700 11px/1.4 {sans};color:{accent};letter-spacing:.12em;text-transform:uppercase;">
      No. {i:02d} &nbsp;&middot;&nbsp; {e(item["access"])}
    </div>{image}
    <h2 style="margin:0 0 8px;font:700 23px/1.2 {serif};color:#121212;">
      <a href="{e(item["url"])}" style="color:#121212;text-decoration:none;">{e(item["name"])}</a>
    </h2>
    <p style="margin:0 0 12px;font:italic 16px/1.5 {serif};color:#5A5A5A;">{e(item["what"])}</p>
    <p style="margin:0 0 16px;font:16px/1.6 {serif};color:#333333;">{e(item["pitch"])}</p>
    <div style="margin:0 0 8px;font:700 11px/1.4 {sans};color:#121212;letter-spacing:.12em;">PUT IT TO WORK</div>
    <ul style="margin:0 0 14px;padding-left:20px;font:15px/1.55 {serif};color:#333333;">{apps}</ul>
    <a href="{e(item["url"])}" style="font:600 11px/1.4 {sans};color:{accent};letter-spacing:.08em;text-transform:uppercase;text-decoration:none;">{e(domain)} &#8599;</a>
  </div>""")

    preheader = " · ".join(item["name"] for item in items)
    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#FFFFFF;color-scheme:light;">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;color:#FFFFFF;">
  {e(preheader)}&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;
</div>
<div style="max-width:600px;margin:0 auto;padding:30px 20px 24px;">
  <div style="text-align:center;padding:0 0 18px;">
    <img src="{LOGO_URL}" width="72" height="72" alt="Wausau Pilot &amp; Review"
         style="display:block;margin:0 auto 12px;width:72px;height:72px;">
    <h1 style="margin:0 0 6px;font:700 34px/1.1 {serif};color:#121212;">{e(edition["title"])}</h1>
    <div style="font:600 11px/1.5 {sans};color:#727272;letter-spacing:.14em;text-transform:uppercase;">
      {today:%A, %B %d, %Y} &nbsp;&middot;&nbsp; {len(items)} finds
    </div>
  </div>
  <div style="border-top:3px solid #121212;"></div>
  {"".join(blocks)}
  <div style="padding:18px 8px 0;text-align:center;font:12px/1.7 {sans};color:#8A8A8A;">
    Generated by wpr-ai-digest &middot; research by {e(MODEL)} with web search<br>
    edit {e(edition["context"])} to change what gets surfaced
  </div>
</div>
</body></html>"""


def send(subject: str, body_html: str, to: str) -> None:
    user, password = env("SMTP_USER"), env("SMTP_PASSWORD")
    msg = MIMEText(body_html, "html", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    positional = [a for a in sys.argv[1:] if not a.startswith("-")]
    edition = EDITIONS[positional[0] if positional else "wpr"]
    today = date.today()
    context = (ROOT / edition["context"]).read_text(encoding="utf-8")
    seen_path = ROOT / edition["seen"]
    seen = json.loads(seen_path.read_text(encoding="utf-8"))

    items = research(anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY")), context, seen, edition["max_cost"])
    for item in items:
        item["image"] = fetch_og_image(item["url"])
    body = render(items, today, edition)

    if dry_run:
        out = ROOT / "digest-preview.html"
        out.write_text(body, encoding="utf-8")
        print(f"dry run: wrote {out}")
        return

    subject = f"{edition['subject']} — {items[0]['name']} + {len(items) - 1} more ({today:%b %d})"
    send(subject, body, env("DIGEST_TO"))
    seen.extend({"name": it["name"], "url": it["url"], "date": today.isoformat()} for it in items)
    seen_path.write_text(json.dumps(seen, indent=2) + "\n", encoding="utf-8")
    print(f"sent {len(items)} items to {env('DIGEST_TO')}")


if __name__ == "__main__":
    main()