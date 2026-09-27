# Who this is for

Rowan Flynn, the solo developer behind Wausau Pilot & Review's fleet of 50+ GitHub repos: Python scrapers on GitHub Actions crons that publish JSON, React/Vite widgets deployed to GitHub Pages and embedded in WordPress, and several automated email pipelines. When a cron fails quietly, readers see stale data and nobody says a word. This weekly check lists what is broken, ranked by what it costs, with a likely cause and a first step for each.

# How to rank

1. **Revenue and reader-facing products first:** the jobs board (Stripe), election tools, the newsletter pipeline, and live trackers embedded on the site (Ledgers, court, permit, property, Coming Soon, events calendar, sports and price widgets).
2. **Data other tools depend on:** property transactions, Coming Soon, and the Ledgers feed the Ledger Brief and Sponsor Leads digests — breakage there spreads.
3. **Internal tooling and experiments** next; demos and prototypes (e.g. anything named demo) last.

Kinds, and how to read them:
- **Failing** — the latest runs failed. A long streak means the output is stale; say how long.
- **Stopped firing** — a scheduled workflow that still has a schedule but hasn't run in far longer than usual.
- **Disabled by GitHub** — GitHub switches off scheduled workflows in public repos after 60 days without a commit. The fix is to re-enable it (`gh workflow enable`) and keep the repo active, e.g. by having the cron commit its data or adding a keepalive.
- **Security** — open high or critical Dependabot alerts.

Be concrete and brief; Rowan will open the run log for details. A guessed cause must be labeled as a guess.
