"""Weekly AI tools digest for WPR.

research() -> render() -> send(), then record what was covered so next week skips it.
"""

import html
import json
import os
import smtplib
import sys
from datetime import date
from email.mime.text import MIMEText
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent
CONTEXT = (ROOT / "context.md").read_text(encoding="utf-8")
SEEN_PATH = ROOT / "seen.json"

MODEL = "claude-sonnet-5"
MAX_SEARCHES = 15
MIN_ITEMS, MAX_ITEMS = 3, 6

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_prompt(seen: list[dict]) -> str:
    already = "\n".join(f"- {s['name']}" for s in seen) or "- (none yet)"
    return f"""{CONTEXT}

# Already covered in previous digests (do not repeat)
{already}

# Task

Today is {date.today():%A, %B %d, %Y}. Search the web for AI tools, models, APIs, and product features
announced or materially updated in the last 10 days. Use several distinct searches across the categories
under "Worth surfacing" — do not stop after one or two queries. Prefer primary sources (vendor blogs,
GitHub releases, docs, changelogs) and journalism-sector outlets over aggregators.

Select {MIN_ITEMS}–{MAX_ITEMS} finds. Rank by how directly a solo developer at a local newsroom could use
it this month. Every application must name a specific WPR build from the list above or a concrete
newsroom workflow — no generic "could help with content".

Respond with ONLY a JSON object, no prose before or after, no markdown fences:

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


def research(client: anthropic.Anthropic, seen: list[dict]) -> list[dict]:
    messages = [{"role": "user", "content": build_prompt(seen)}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}]

    while True:
        response = client.messages.create(model=MODEL, max_tokens=8000, messages=messages, tools=tools)
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        if response.stop_reason != "end_turn":
            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")
        break

    searches = response.usage.server_tool_use.web_search_requests
    print(f"model={MODEL} searches={searches} in={response.usage.input_tokens} out={response.usage.output_tokens}")

    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise RuntimeError("Response contained no text block")
    items = json.loads(text_blocks[-1].strip())["items"]
    if not MIN_ITEMS <= len(items) <= MAX_ITEMS:
        raise RuntimeError(f"Expected {MIN_ITEMS}–{MAX_ITEMS} items, got {len(items)}")
    return items


def render(items: list[dict], today: date) -> str:
    e = html.escape
    cards = []
    for i, item in enumerate(items, 1):
        apps = "".join(f"<li>{e(a)}</li>" for a in item["applications"])
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
      <a href="{e(item["url"])}" style="color:#3A867C;">{e(item["url"])}</a>
    </p>
  </div>""")

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F6F2E9;">
<div style="max-width:640px;margin:0 auto;padding:32px 24px;">
  <div style="font:500 12px/1.3 'JetBrains Mono',Consolas,monospace;color:#3A867C;letter-spacing:.08em;">WAUSAU PILOT &amp; REVIEW</div>
  <h1 style="margin:4px 0 2px;font:600 30px/1.15 Fraunces,Georgia,serif;color:#1F1E1B;">AI Digest</h1>
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
    today = date.today()
    seen = json.loads(SEEN_PATH.read_text(encoding="utf-8"))

    items = research(anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY")), seen)
    body = render(items, today)

    if dry_run:
        out = ROOT / "digest-preview.html"
        out.write_text(body, encoding="utf-8")
        print(f"dry run: wrote {out}")
        return

    send(f"WPR AI Digest — {today:%b %d, %Y}", body, env("DIGEST_TO"))
    seen.extend({"name": it["name"], "url": it["url"], "date": today.isoformat()} for it in items)
    SEEN_PATH.write_text(json.dumps(seen, indent=2) + "\n", encoding="utf-8")
    print(f"sent {len(items)} items to {env('DIGEST_TO')}")


if __name__ == "__main__":
    main()
