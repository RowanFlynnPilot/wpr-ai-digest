# Who this digest is for

Rowan Flynn — technical lead and editorial contributor at Wausau Pilot & Review (WPR), a nonprofit local newsroom in Wausau, Wisconsin covering Marathon County. Also co-builds the Old English Collective (OEC), a 501(c)(3) making shared infrastructure tools for local newsrooms. Solo developer; ships fast; allergic to overengineering.

# Stack (what a tool has to fit into)

- Python scrapers → static JSON → GitHub Actions (cron) → React/Vite → GitHub Pages → embedded in WordPress via iframe
- Supabase (Postgres + RLS + Deno edge functions) for anything stateful; Stripe for paid features
- Claude API (Haiku for high-volume extraction, Claude Code for development); anthropic SDK in Python
- Scraping: Playwright, curl_cffi, pdfplumber, Webshare residential proxies
- Email: MailerLite (newsletters), WordPress/Noptin (legacy sends)
- Analytics: Plausible. Audio: RTL-SDR + trunk-recorder + faster-whisper.
- Windows/PowerShell dev environment

# Live and recent WPR builds (name a specific one when pitching an application)

Accountability archives ("Ledgers"):
- The Care Ledger — Wisconsin DQA assisted-living facility inspection/violation archive
- The Cleanup Ledger — BRRTS contamination sites + continuing obligations
- The Rent Ledger — eviction filings + landlord accountability
- The Settlement Ledger — opioid settlement fund tracker
- The Watch Ledger — Flock/ALPR surveillance camera map + agency roster
- Ledger Framework (OEC) — open-source "accountability archive in a box" extracted from the above

Civic / public-records trackers:
- Gavel (marathon-meetings) — civic meeting intelligence: agendas, minutes, recordings → summaries, alerts; being productized as a managed instance for other newsrooms
- Court tracker (WCCA RSS, curated watchlist, presumption-of-innocence policy)
- Permit tracker (pdfplumber parsing of municipal PDFs) and property transactions scraper (Wisconsin DOR TAP portal)
- "Coming Soon" tracker — merges permit, property-sale, and license signals to surface what's opening in local buildings
- TIF district scorecard, property tax assessment equity study (IAAO stats), Follow the Money budget widget
- PFAS/drinking water compliance tracker (DNR + EPA SDWIS, 730 systems)
- Education data tracker (ACT, dropout rates) — Marathon County first, statewide path
- Communicable disease / vaccine-preventable illness tracker (scoping)

Breaking news / editor tooling:
- Fire Watch — Raspberry Pi + RTL-SDR monitor of fire/EMS dispatch; faster-whisper transcription + Claude Haiku classification; alerts the editor on major incidents
- Obituary platform — scraping with Chrome impersonation, Haiku extraction, schema.org static pages
- Election results widget (live county results) and multi-tenant voter guide
- Road/traffic conditions tool on the 511WI API (scoping v1)
- Newsletter pipeline — auto-generated daily campaigns replacing hand-built Afternoon/AM Updates

Reader engagement / revenue:
- Sponsor analytics reporting on Plausible (proves ad value to sponsors)
- Cheese Census (statewide reader tool, sponsor play), cutest-pet contest (paid voting), Best of Wausau ballot
- Jobs board (Supabase + Stripe), Community Board, community events calendar, Happy Hour Finder, Fish Fry Finder
- Sports widgets (Woodchucks, Cyclones, Badgers, Brewers, Bucks, high school sports) hitting public APIs browser-direct
- Finance calculators aimed at credit-union sponsors; grocery and gas price trackers
- Audience growth via Reddit (r/Wisconsin)

# What counts as a useful find

Worth surfacing (favor step changes — things that make a previously impractical build feasible, replace a whole workflow, or open a new category of tool; a price or quota change only matters as supporting context on an otherwise significant find):
- New models, APIs, and SDK capabilities (Anthropic, OpenAI, Google, Mistral, open-weights) that change what a solo developer can build — new modalities, agentic capabilities, structured output, vision/PDF, audio, long context
- Agentic coding tools and Claude Code / MCP ecosystem changes that speed up a solo developer
- Document AI: OCR, PDF/table extraction, scanned-record parsing, entity extraction, dedup/record linkage
- Speech: transcription, diarization, radio/meeting audio — anything that improves Fire Watch or Gavel
- Journalism-specific AI tools and open-source newsroom projects (Nieman Lab, Hacks/Hackers, INN, LION, Journalist's Resource, Big Local News, Knight Lab, AP, Reuters Institute)
- Public-records and civic-data tooling: FOIA helpers, meeting summarizers, court/permit/campaign-finance parsers
- Data viz, mapping, and embeddable-widget tooling that fits a static-site pipeline
- Scraping, anti-bot, and monitoring tooling
- Email/newsletter AI features relevant to MailerLite-scale publishers
- Grants, fellowships, or funder programs specifically for AI in local news (only if newly announced and open)

Not worth surfacing:
- Incremental price drops, quota bumps, and minor version updates that add no new capability
- Enterprise-only products with no self-serve access or public pricing
- Funding rounds, executive hires, and opinion pieces with no tool to try
- Consumer chatbots, image generators, and productivity apps with no newsroom angle
- Anything already listed under "already covered"
