# wpr-ai-digest

Two weekly digest emails from one pipeline, selected by `python digest.py [edition]`:
- `wpr` (default) — Fridays, to Rowan: new AI tools/features from the past ~10 days with applications tied to specific WPR builds. `context.md`, `seen.json`, `.github/workflows/digest.yml`.
- `industry` — Mondays, to Rowan + editor: AI in local journalism generally (newsroom tools, case studies, grants, platform shifts, ethics), written for an editorial reader. `context-industry.md`, `seen-industry.json`, `.github/workflows/digest-industry.yml`.
- `tools` — Wednesdays, to Rowan + editor: new and trending AI tools and plug-ins anyone can use same-day (apps, WordPress plugins, extensions, no-code automation), general reader. $4 cost cap (others $3). `context-tools.md`, `seen-tools.json`, `.github/workflows/digest-tools.yml`.
- `ledgers` — Tuesdays, to Rowan + editor: assignment memo diffed from WPR's own tracker JSONs (`LEDGER_SOURCES` in digest.py) — Python fetches and diffs against `ledgers-state.json`, Claude writes the brief (no web search, ~$0.15, $1 cap). Skips the send when nothing changed. `context-ledgers.md`, `seen-ledgers.json`, `.github/workflows/digest-ledgers.yml`.
- `grants` — 1st of each month, to Rowan + editor: currently-open grants/fellowships for small nonprofit newsrooms, deadline-sorted, deadlines confirmed via fetch. `context-grants.md`, `seen-grants.json`, `.github/workflows/digest-grants.yml`.

Each edition's context file owns its entire selection framing, including the "How to rank and pitch" section the code prompt defers to.

`hub.py` regenerates `docs/index.html` — a static status hub (per edition: schedule, recipients, last sent, item history) derived entirely from repo state; each workflow reruns it after a send. New editions following the `digest-{key}.yml` convention appear automatically.

## How it works
- `digest.py` — three functions, one path: `research()` (Claude + server-side web search/fetch → JSON), `render()` (inline-styled HTML in WPR colors), `send()` (Gmail SMTP). `main()` wires them and appends covered items to `seen.json`.
- `context.md` — everything the model knows about WPR: stack, project list, what counts as a good find. **Edit this, not the prompt in code**, when a new project ships or priorities change.
- Recipients live in `DIGEST_TO` in the workflow env, comma-separated; `send()` puts the list in the To header and `send_message` delivers to each.
- `seen.json` — names/urls already surfaced; fed back into the prompt so weeks don't repeat. Committed by the workflow after each send.
- Workflows run at **11:47 UTC** (6:47am CDT), deliberately off the top of the hour — GitHub delays `:00` crons by hours. All five share a `concurrency` group so same-day sends queue instead of racing on the `seen`/hub commit. Each has a `dry_run` dispatch input (research + render, preview as artifact, no send, no commit).
- `min_items` per edition (default 3) — grants and ledgers use 1, since a thin month/week should still send rather than fail. `validate_items()` rejects a malformed answer before anything is rendered or sent.
- Ledgers: one unreachable tracker is reported in the log and in the email masthead, its previous hashes carried forward; only all-sources-down fails the run.
- `requirements.txt` pins `anthropic>=1,<2` — a major SDK bump must be deliberate, never picked up by a cron.

## Secrets (repo → Settings → Secrets and variables → Actions)
- `ANTHROPIC_API_KEY`
- `SMTP_USER` — `rowan.flynn@wausaupilotandreview.com` (the sending account)
- `SMTP_PASSWORD` — a Google app password for that account (requires 2-Step Verification on)

## Local
`python -m pip install -r requirements.txt; $env:ANTHROPIC_API_KEY="..."; python digest.py --dry-run` → writes `digest-preview.html`, sends nothing, doesn't touch `seen.json`.

## Principles
No fallbacks, fail loud. Missing env var, bad JSON, wrong item count, or an unexpected stop_reason all raise. If a run fails, the workflow shows red and no email goes out — that's the signal.

Cost: the research loop sums real usage (cache writes/reads, output, search fees) across every pause_turn round and raises past the edition's `max_cost` ($3–4). Runs use the full search/fetch budget every time (25/16), so item count is budget-bound — raise those before loosening the quality bar. Pricing constants sit next to `MODEL` in digest.py — update both together. Prompt caching keeps continuation rounds at ~10% input price; `FETCH_CONTENT_TOKENS` caps how much of a fetched page enters context.
