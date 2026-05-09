# API Setup — homeowner-agent

## Yelp Fusion API (free tier, recommended)

1. Go to https://developer.yelp.com and create an account
2. Create an app to get an API key
3. Free tier: 500 calls/day, returns business name, rating, reviews, phone, address, price tier
4. Store key in OpenClaw secrets or pass via `--yelp-key`

**Endpoint used:** `GET /v3/businesses/search`  
**Key params:** `term`, `location`, `limit`, `sort_by`

---

## Google Places API (paid, ~$0.017/request)

1. Go to https://console.cloud.google.com
2. Enable the "Places API"
3. Create an API key under Credentials
4. Free monthly credit of $200 covers ~11,700 requests
5. Store key in OpenClaw secrets or pass via `--google-key`

**Endpoint used:** `GET /maps/api/place/textsearch/json`  
**Key params:** `query`, `key`, `type=establishment`

---

## Angi (no API — web scrape)

- No public API available
- Scrape targets: `https://www.angi.com/companylist/us/<location>/<category>.htm`
- Angi frequently returns 403; results are best-effort
- If scraping fails, the skill returns a direct link to the Angi search page
- For reliable results, users should visit Angi directly

---

## Thumbtack (no API — web scrape)

- No public API; quotes require account login
- Scrape targets: `https://www.thumbtack.com/k/<task>/near/<location>/`
- Extracts JSON-LD or `__NEXT_DATA__` embedded in page when available
- If scraping fails, returns a direct link to the Thumbtack search page
- Quotes are only visible after logging in on Thumbtack

---

## Storing Keys in OpenClaw

Once you have keys, store them so the skill can retrieve them:

```
openclaw secrets set YELP_API_KEY <your-key>
openclaw secrets set GOOGLE_PLACES_KEY <your-key>
```

The skill reads these from the environment automatically when running the script.

---

## Source Reliability Summary

| Source     | Data Quality | Quotes Available | API Available |
|------------|-------------|-----------------|---------------|
| Yelp       | ✅ High      | ❌ No (ratings only) | ✅ Yes (free) |
| Google     | ✅ High      | ❌ No (ratings only) | ✅ Yes (paid) |
| Angi       | ⚠️ Variable  | ✅ Sometimes     | ❌ No         |
| Thumbtack  | ⚠️ Variable  | ✅ With login    | ❌ No         |
