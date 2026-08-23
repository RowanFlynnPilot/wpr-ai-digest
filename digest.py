"""Weekly AI tools digest for WPR.

research() -> render() -> send(), then record what was covered so next week skips it.
"""

import html
import json
import os
import re
import smtplib
import sys
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import urlparse

import anthropic

ROOT = Path(__file__).parent

EDITIONS = {
    "wpr": {"context": "context.md", "seen": "seen.json",
            "title": "AI Digest", "subject": "WPR AI Digest"},
    "industry": {"context": "context-industry.md", "seen": "seen-industry.json",
                 "title": "AI in Local News", "subject": "AI in Local News"},
}

MODEL = "claude-opus-5"
MAX_SEARCHES = 15
MAX_FETCHES = 8
FETCH_CONTENT_TOKENS = 10_000
MIN_ITEMS, MAX_ITEMS = 3, 6

# claude-opus-5 pricing ($/MTok) plus $10 per 1k web searches — keep in sync with MODEL
IN_RATE, OUT_RATE = 5.00, 25.00
CACHE_WRITE_RATE, CACHE_READ_RATE = 6.25, 0.50
SEARCH_COST = 0.01
MAX_COST_USD = 3.00
MAX_ROUNDS = 8

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587


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

Select {MIN_ITEMS}–{MAX_ITEMS} finds. Rank the items and write the pitch and applications exactly as
the "How to rank and pitch" section above directs — no generic "could help with content".

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


def research(client: anthropic.Anthropic, context: str, seen: list[dict]) -> list[dict]:
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
        if cost > MAX_COST_USD:
            raise RuntimeError(f"Run cost ${cost:.2f} exceeded the ${MAX_COST_USD:.2f} cap — aborting")
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


def render(items: list[dict], today: date, title: str) -> str:
    e = html.escape
    cards = []
    for i, item in enumerate(items, 1):
        apps = "".join(f"<li>{e(a)}</li>" for a in item["applications"])
        domain = urlparse(item["url"]).netloc.removeprefix("www.")
        cards.append(f"""
  <div style="padding:20px 0;border-top:1px solid #E3DCCF;">
    <div style="font:500 12px/1.3 'JetBrains Mono',Consolas,monospace;color:#3A867C;letter-spacing:.04em;">
      {i:02d} &nbsp;·&nbsp; {e(item["access"]).upper()}
    </div>
    <h2 style="margin:6px 0 4px;font:600 20px/1.25 Fraunces,Georgia,serif;color:#1F1E1B;">
      <a href="{e(item["url"])}" style="color:#1F1E1B;text-decoration:none;">{e(item["name"])}</a>
    </h2>
    <p style="margin:0 0 10px;font:15px/1.45 'Public Sans',-apple-system,'Segoe UI',sans-serif;color:#5C5A54;">{e(item["what"])}</p>
    <p style="margin:0 0 10px;font:15px/1.5 'Public Sans',-apple-system,'Segoe UI',sans-serif;color:#1F1E1B;">{e(item["pitch"])}</p>
    <div style="font:500 12px/1.3 'JetBrains Mono',Consolas,monospace;color:#3A867C;letter-spacing:.04em;">PUT IT TO WORK</div>
    <ul style="margin:6px 0 0;padding-left:20px;font:15px/1.5 'Public Sans',-apple-system,'Segoe UI',sans-serif;color:#1F1E1B;">{apps}</ul>
    <p style="margin:10px 0 0;font:13px/1.4 'Public Sans',-apple-system,'Segoe UI',sans-serif;">
      <a href="{e(item["url"])}" style="color:#3A867C;text-decoration:none;">{e(domain)} &#8599;</a>
    </p>
  </div>""")

    preheader = " · ".join(item["name"] for item in items)
    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=JetBrains+Mono:wght@500&family=Public+Sans:wght@400;500&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#F6F2E9;color-scheme:light;">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;color:#F6F2E9;">
  {e(preheader)}&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;&nbsp;&#8204;
</div>
<div style="max-width:640px;margin:0 auto;padding:32px 24px;">
  <div style="font:500 12px/1.3 'JetBrains Mono',Consolas,monospace;color:#3A867C;letter-spacing:.08em;">WAUSAU PILOT &amp; REVIEW</div>
  <h1 style="margin:4px 0 2px;font:600 30px/1.15 Fraunces,Georgia,serif;color:#1F1E1B;">{e(title)}</h1>
  <div style="margin:0 0 18px;font:14px/1.4 'Public Sans',-apple-system,'Segoe UI',sans-serif;color:#5C5A54;">
    {today:%A, %B %d, %Y} &nbsp;·&nbsp; {len(items)} finds worth a look this week
  </div>
  {"".join(cards)}
  <div style="margin-top:28px;padding-top:14px;border-top:2px solid #3A867C;font:12px/1.5 'Public Sans',-apple-system,'Segoe UI',sans-serif;color:#8A877F;">
    Generated by wpr-ai-digest · research by {e(MODEL)} with web search · edit context.md to change what gets surfaced
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

    items = research(anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY")), context, seen)
    body = render(items, today, edition["title"])

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