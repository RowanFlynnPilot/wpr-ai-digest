# wpr-ai-digest

Weekly Friday email to Rowan: new AI tools/features from the past ~10 days, each with a short pitch and concrete applications tied to WPR builds.

## How it works
- `digest.py` — three functions, one path: `research()` (Claude + server-side web search/fetch → JSON), `render()` (inline-styled HTML in WPR colors), `send()` (Gmail SMTP). `main()` wires them and appends covered items to `seen.json`.
- `context.md` — everything the model knows about WPR: stack, project list, what counts as a good find. **Edit this, not the prompt in code**, when a new project ships or priorities change.
- Recipients live in `DIGEST_TO` in the workflow env, comma-separated; `send()` puts the list in the To header and `send_message` delivers to each.
- `seen.json` — names/urls already surfaced; fed back into the prompt so weeks don't repeat. Committed by the workflow after each send.
- `.github/workflows/digest.yml` — cron Fridays 13:00 UTC + manual `workflow_dispatch`.

## Secrets (repo → Settings → Secrets and variables → Actions)
- `ANTHROPIC_API_KEY`
- `SMTP_USER` — `rowan.flynn@wausaupilotandreview.com` (the sending account)
- `SMTP_PASSWORD` — a Google app password for that account (requires 2-Step Verification on)

## Local
`python -m pip install -r requirements.txt; $env:ANTHROPIC_API_KEY="..."; python digest.py --dry-run` → writes `digest-preview.html`, sends nothing, doesn't touch `seen.json`.

## Principles
No fallbacks, fail loud. Missing env var, bad JSON, wrong item count, or an unexpected stop_reason all raise. If a run fails, the workflow shows red and no email goes out — that's the signal.
