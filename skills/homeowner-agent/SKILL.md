---
name: homeowner-agent
description: Find home service professionals and quotes for a given task and location. Searches Yelp, Angi, Thumbtack, and Google for contractors, handymen, plumbers, electricians, and other service providers. Use when a user asks to find someone to do a home repair, maintenance, or improvement task — e.g. "find someone to fix my roof", "get quotes for painting my house", "who can fix my leaky faucet in Austin TX". Output is a formatted list suitable for chat delivery.
---

# Homeowner Agent

Searches Yelp, Angi, Thumbtack, and Google for home service professionals matching a task and location.

## Quick Start

Run `scripts/find_pros.py` with task and location. API keys are optional but improve results.

```bash
python3 scripts/find_pros.py \
  --task "fix a leaky faucet" \
  --location "Seattle, WA" \
  --yelp-key "$YELP_API_KEY" \
  --google-key "$GOOGLE_PLACES_KEY"
```

Output is formatted text ready to paste into any chat channel. Use `--json` for raw data.

## Inputs to Collect

Before running, get from the user:
1. **Task** — what needs doing (be specific: "replace kitchen faucet" > "plumbing")
2. **Location** — city and state, or zip code

## API Keys

- **Yelp** (`YELP_API_KEY`) and **Google Places** (`GOOGLE_PLACES_KEY`) give the best structured results
- If keys aren't set yet, the script returns direct search links for those sources as fallback
- Keys can be stored with `openclaw secrets set YELP_API_KEY <key>`
- See `references/api-setup.md` for setup instructions for each source

## Source Behavior

| Source    | Method        | Returns                        |
|-----------|--------------|-------------------------------|
| Yelp      | API          | Name, rating, phone, address, price tier |
| Google    | API          | Name, rating, address, Maps link |
| Angi      | Web scrape   | Name, rating (best-effort; may fall back to link) |
| Thumbtack | Web scrape   | Name, rating (best-effort; quotes need login) |

Angi and Thumbtack block scrapers aggressively — always expect occasional fallback-to-link behavior. That's normal, not a bug.

## Output Format

The script outputs a formatted text block with:
- Task and location header
- Results grouped by source
- Name, rating, phone, address, and URL per pro
- Footer note about contacting pros directly for quotes

This format is designed for text channel delivery (WhatsApp, Telegram, Discord). When you have a channel set up, you can pipe the output directly to it.

## When Keys Are Missing

If the user hasn't provided API keys yet, run the script anyway — it returns Yelp and Google search links plus best-effort Angi/Thumbtack results. Remind the user to check `references/api-setup.md` to get their keys.
