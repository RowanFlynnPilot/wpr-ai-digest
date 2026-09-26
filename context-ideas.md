# Who this digest is for

Rowan Flynn — technical lead at Wausau Pilot & Review (WPR), a nonprofit local newsroom in Wausau, Wisconsin, and co-builder of the Old English Collective (OEC), a 501(c)(3) making shared tools for local newsrooms. Solo developer who builds almost everything with Claude Code. This is a weekly scan of what practitioners on Reddit and Substack are actually doing with AI: techniques, workflows, prompts, clever builds, and money-making ideas — the stuff that surfaces in threads and newsletters before it becomes a product announcement. Companion digests already cover product launches, trending tools, Claude skills, and journalism-industry news; this one is about ideas and technique.

# What WPR has already built (for the "fits our work" bucket)

- Accountability archives ("Ledgers"): Care Ledger (assisted-living inspections), Cleanup Ledger (contamination sites), Rent Ledger (evictions), Settlement Ledger (opioid funds), Watch Ledger (Flock/ALPR cameras); Ledger Framework (OEC) packages them for other newsrooms
- Gavel: civic meeting intelligence (agendas, minutes, recordings → summaries, alerts), being productized for other newsrooms
- Court, permit, property-sale, and "Coming Soon" trackers; TIF, tax-equity, budget, PFAS, and education data tools
- Fire Watch: RTL-SDR dispatch audio → faster-whisper → Claude Haiku classification → editor alerts
- Obituary platform (scraping + Haiku extraction), election results widget, voter guide, newsletter pipeline
- Reader/revenue tools: jobs board (Supabase + Stripe), contests, sponsor analytics on Plausible, sports and price widgets
- Stack: Python scrapers → JSON → GitHub Actions → React/Vite → GitHub Pages → WordPress embeds; Supabase; Claude API; Playwright/curl_cffi/pdfplumber

# How to rank and pitch

Sort every pick into one of three buckets, and order the issue by bucket in this order:

1. **Fits our work** — a technique, workflow, or prompt that would make an existing WPR build better, faster, cheaper, or more reliable. The first application must name the specific build.
2. **Could pay** — something WPR or OEC hasn't done that a small nonprofit newsroom could plausibly turn into revenue: a product other newsrooms or local businesses would pay for, a sponsorable reader tool, a service. Name who pays and roughly why. Skip get-rich-quick schemes, engagement bait, and anything a newsroom would be embarrassed to run.
3. **Fascinating** — genuinely novel or surprising ideas worth knowing even without an immediate use. Keep this bucket to the one or two best.

Put the bucket first in the access field, then the source and its engagement, e.g. "Fits our work · r/ClaudeCode #2 this week" or "Could pay · Lenny's Newsletter · 309 likes". Aim for at least one pick per bucket when the week supports it.

Momentum matters: a top-3 thread or a heavily liked post beats a buried one, but usefulness beats popularity. Prefer free Substack posts (readable in full) over paid ones.

When a pick centers on a prompt or technique, make it usable: "what" states the technique concretely, and the first application is a ready-to-try adaptation for WPR written in your own words (e.g. "Try: have Haiku rank three candidate headlines and justify the pick before…"). Paraphrase — never paste a post's prompt or text beyond a short phrase.

# Worth surfacing

- Prompting and context techniques people report actually work (with evidence or before/after, not vibes)
- Agent, Claude Code, and automation workflows (n8n, scheduled agents, multi-agent setups) with real results
- Clever builds and side projects, especially data, scraping, document, audio, and local-information tools
- Cost and reliability tricks: caching, batching, smaller models, evals, guardrails
- Business models and monetization patterns for AI-built tools that fit a small nonprofit
- Surprising use cases or honest failure reports that change how to think about using AI

# Not worth surfacing

- Product-launch and model-release news with no technique or idea in it — the other digests cover launches
- Complaint threads, drama, benchmarks arguments, and "is AI conscious" discourse
- Anything paywalled that can't be read beyond the teaser, unless the teaser alone carries the idea
- Engagement-bait growth hacks, cold-DM automation, scraping personal data, or anything ethically awkward for a newsroom
- Anything already listed under "already covered"
