#!/usr/bin/env python3
"""
find_pros.py — Search for home service professionals across Yelp, Angi, Thumbtack, and Google.

Usage:
    python3 find_pros.py --task "fix a leaky faucet" --location "Seattle, WA" [--yelp-key KEY] [--google-key KEY]

Output: JSON list of professionals with name, source, rating, phone, url, and notes.
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error

# ── Yelp ──────────────────────────────────────────────────────────────────────

def search_yelp(task: str, location: str, api_key: str) -> list[dict]:
    """Search Yelp Fusion API for businesses matching the task."""
    params = urllib.parse.urlencode({
        "term": task,
        "location": location,
        "limit": 5,
        "sort_by": "best_match",
    })
    url = f"https://api.yelp.com/v3/businesses/search?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return [{"error": f"Yelp API error {e.code}: {e.reason}"}]
    except Exception as e:
        return [{"error": f"Yelp fetch failed: {e}"}]

    results = []
    for biz in data.get("businesses", []):
        results.append({
            "source": "Yelp",
            "name": biz.get("name"),
            "rating": biz.get("rating"),
            "review_count": biz.get("review_count"),
            "phone": biz.get("display_phone") or biz.get("phone"),
            "address": ", ".join(biz.get("location", {}).get("display_address", [])),
            "url": biz.get("url"),
            "price": biz.get("price"),
            "categories": [c["title"] for c in biz.get("categories", [])],
        })
    return results


# ── Google Places ──────────────────────────────────────────────────────────────

def search_google(task: str, location: str, api_key: str) -> list[dict]:
    """Search Google Places Text Search API."""
    params = urllib.parse.urlencode({
        "query": f"{task} near {location}",
        "key": api_key,
        "type": "establishment",
    })
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return [{"error": f"Google fetch failed: {e}"}]

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        return [{"error": f"Google API status: {data.get('status')} — {data.get('error_message', '')}"}]

    results = []
    for place in data.get("results", [])[:5]:
        results.append({
            "source": "Google",
            "name": place.get("name"),
            "rating": place.get("rating"),
            "review_count": place.get("user_ratings_total"),
            "address": place.get("formatted_address"),
            "url": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
            "open_now": place.get("opening_hours", {}).get("open_now"),
        })
    return results


# ── Angi (web scrape) ─────────────────────────────────────────────────────────

def search_angi(task: str, location: str) -> list[dict]:
    """Best-effort scrape of Angi search results page."""
    import html
    import re

    # Angi URL format: /companylist/us/<city-state-slug>/<category-slug>.htm
    query_slug = task.lower().replace(" ", "-")
    loc_slug = location.lower().replace(", ", "-").replace(" ", "-")
    url = f"https://www.angi.com/companylist/us/{loc_slug}/{query_slug}.htm"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; HomePro/1.0)",
            "Accept": "text/html",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return [{"source": "Angi", "error": f"Scrape failed: {e}", "url": url, "note": "Visit Angi directly for results."}]

    # Extract business names from JSON-LD or structured patterns
    results = []
    # Try JSON-LD embedded data
    ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    for block in ld_matches:
        try:
            obj = json.loads(block)
            items = obj if isinstance(obj, list) else [obj]
            for item in items:
                if item.get("@type") in ("LocalBusiness", "HomeAndConstructionBusiness", "Plumber", "Electrician", "GeneralContractor"):
                    results.append({
                        "source": "Angi",
                        "name": item.get("name"),
                        "rating": item.get("aggregateRating", {}).get("ratingValue"),
                        "review_count": item.get("aggregateRating", {}).get("reviewCount"),
                        "phone": item.get("telephone"),
                        "address": item.get("address", {}).get("streetAddress"),
                        "url": item.get("url") or url,
                    })
        except Exception:
            continue

    if not results:
        # Fallback: return a helpful pointer
        results.append({
            "source": "Angi",
            "note": "Angi blocks automated scraping. Visit the URL below for results.",
            "url": url,
        })

    return results[:5]


# ── Thumbtack (web scrape) ────────────────────────────────────────────────────

def search_thumbtack(task: str, location: str) -> list[dict]:
    """Best-effort scrape of Thumbtack search results."""
    import re

    query_slug = task.lower().replace(" ", "-")
    loc_slug = location.lower().replace(", ", "-").replace(" ", "-")
    url = f"https://www.thumbtack.com/k/{query_slug}/near/{loc_slug}/"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; HomePro/1.0)",
            "Accept": "text/html",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return [{"source": "Thumbtack", "error": f"Scrape failed: {e}", "url": url, "note": "Visit Thumbtack directly for quotes."}]

    results = []
    # Try JSON-LD
    ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
    for block in ld_matches:
        try:
            obj = json.loads(block)
            items = obj if isinstance(obj, list) else [obj]
            for item in items:
                if item.get("@type") in ("LocalBusiness", "Service", "Person"):
                    results.append({
                        "source": "Thumbtack",
                        "name": item.get("name"),
                        "rating": item.get("aggregateRating", {}).get("ratingValue"),
                        "review_count": item.get("aggregateRating", {}).get("reviewCount"),
                        "url": item.get("url") or url,
                    })
        except Exception:
            continue

    # Try __NEXT_DATA__ JSON embedded in page
    if not results:
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', body, re.DOTALL)
        if match:
            try:
                nd = json.loads(match.group(1))
                pros = nd.get("props", {}).get("pageProps", {}).get("pros", [])
                for pro in pros[:5]:
                    results.append({
                        "source": "Thumbtack",
                        "name": pro.get("businessName") or pro.get("name"),
                        "rating": pro.get("rating"),
                        "review_count": pro.get("numReviews"),
                        "url": f"https://www.thumbtack.com{pro.get('profileUrl', '')}",
                    })
            except Exception:
                pass

    if not results:
        results.append({
            "source": "Thumbtack",
            "note": "Thumbtack requires login for quotes. Visit the URL below.",
            "url": url,
        })

    return results[:5]


# ── Formatting ────────────────────────────────────────────────────────────────

def format_results(task: str, location: str, all_results: list[dict]) -> str:
    """Format results as a clean text list suitable for chat delivery."""
    lines = [
        f"🏠 *Home Pro Search*",
        f"Task: {task}",
        f"Location: {location}",
        f"{'─' * 40}",
    ]

    by_source = {}
    for r in all_results:
        src = r.get("source", "Unknown")
        by_source.setdefault(src, []).append(r)

    for source, pros in by_source.items():
        lines.append(f"\n📌 *{source}*")
        for i, pro in enumerate(pros, 1):
            if "error" in pro and not pro.get("name"):
                lines.append(f"  ⚠️  {pro['error']}")
                if pro.get("url"):
                    lines.append(f"     {pro['url']}")
                continue
            if "note" in pro and not pro.get("name"):
                lines.append(f"  ℹ️  {pro['note']}")
                if pro.get("url"):
                    lines.append(f"     {pro['url']}")
                continue

            name = pro.get("name", "Unknown")
            rating = pro.get("rating")
            reviews = pro.get("review_count")
            phone = pro.get("phone")
            address = pro.get("address")
            url = pro.get("url")
            price = pro.get("price")
            note = pro.get("note")

            rating_str = f"⭐ {rating}" if rating else ""
            reviews_str = f"({reviews} reviews)" if reviews else ""
            price_str = f" · {price}" if price else ""

            lines.append(f"  {i}. *{name}*{price_str}")
            if rating_str or reviews_str:
                lines.append(f"     {rating_str} {reviews_str}".strip())
            if phone:
                lines.append(f"     📞 {phone}")
            if address:
                lines.append(f"     📍 {address}")
            if url:
                lines.append(f"     🔗 {url}")
            if note:
                lines.append(f"     ℹ️  {note}")

    lines.append(f"\n{'─' * 40}")
    lines.append("Quotes may vary. Contact pros directly to confirm availability and pricing.")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Find home service professionals.")
    parser.add_argument("--task", required=True, help="Task description, e.g. 'fix a leaky faucet'")
    parser.add_argument("--location", required=True, help="Location, e.g. 'Seattle, WA'")
    parser.add_argument("--yelp-key", default="", help="Yelp Fusion API key")
    parser.add_argument("--google-key", default="", help="Google Places API key")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    args = parser.parse_args()

    all_results = []

    if args.yelp_key:
        all_results += search_yelp(args.task, args.location, args.yelp_key)
    else:
        all_results.append({"source": "Yelp", "note": "No API key provided. Set --yelp-key.", "url": f"https://www.yelp.com/search?find_desc={urllib.parse.quote_plus(args.task)}&find_loc={urllib.parse.quote_plus(args.location)}"})

    all_results += search_angi(args.task, args.location)
    all_results += search_thumbtack(args.task, args.location)

    if args.google_key:
        all_results += search_google(args.task, args.location, args.google_key)
    else:
        all_results.append({"source": "Google", "note": "No API key provided. Set --google-key.", "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(args.task + ' near ' + args.location)}"})

    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        print(format_results(args.task, args.location, all_results))


if __name__ == "__main__":
    main()
