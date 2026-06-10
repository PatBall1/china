#!/usr/bin/env python3
"""Flight fare lookup for the China 2026 trip, via the Air Scraper API on RapidAPI.

Skyscanner's official API is partner-only, so this targets the Air Scraper
(apiheya) endpoint on RapidAPI (default host: sky-scrapper.p.rapidapi.com). It
resolves each IATA code to a (skyId, entityId) via /api/v1/flights/searchAirport,
then queries /api/v1/flights/searchFlights. Provide a key in .env (see
.env.example). Without a key the script still prints the planned legs.

Usage:
    conda activate china-trip
    python tools/flight_search.py            # query every leg
    python tools/flight_search.py --leg 1    # query a single leg (1-4)
    python tools/flight_search.py --top 5    # show top N cheapest per leg
    python tools/flight_search.py --dry-run  # just print the legs, no API call

Notes:
- Fares are indicative for comparison only; book directly with the airline.
- The searchFlights endpoint is flaky (intermittent {"status": false} or an
  "incomplete" empty session), so requests are retried; on persistent failure the
  raw JSON is saved to out/raw_leg<N>.json for inspection.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
console = Console()


@dataclass
class Leg:
    n: int
    origin: str  # IATA
    dest: str  # IATA
    date: str  # YYYY-MM-DD
    label: str


# Working-plan legs (edit dates here as the plan firms up).
LEGS = [
    Leg(1, "LHR", "HKG", "2026-06-22", "London -> Hong Kong"),
    Leg(2, "HKG", "KMG", "2026-06-27", "Hong Kong -> Kunming (connect to Jinghong)"),
    Leg(3, "JHG", "PKX", "2026-07-04", "Jinghong -> Beijing Daxing"),
    Leg(4, "PEK", "LHR", "2026-07-07", "Beijing -> London"),
]


def load_config() -> dict:
    load_dotenv(ROOT / ".env")
    return {
        "key": os.getenv("RAPIDAPI_KEY"),
        # Air Scraper (apiheya). Older sky-scanner3 hosts use a different schema.
        "host": os.getenv("RAPIDAPI_SKYSCANNER_HOST", "sky-scrapper.p.rapidapi.com"),
        "country": os.getenv("SKYSCANNER_MARKET", "UK"),
        "currency": os.getenv("SKYSCANNER_CURRENCY", "GBP"),
        "locale": os.getenv("SKYSCANNER_LOCALE", "en-GB"),
    }


def _headers(cfg: dict) -> dict:
    return {"x-rapidapi-key": cfg["key"], "x-rapidapi-host": cfg["host"]}


def resolve_place(cfg: dict, query: str) -> tuple[str, str] | None:
    """Resolve an IATA code to (skyId, entityId) via Air Scraper's searchAirport.

    Prefers the AIRPORT whose skyId matches the IATA query; falls back to the
    first airport, then the first result.
    """
    url = f"https://{cfg['host']}/api/v1/flights/searchAirport"
    try:
        r = requests.get(url, headers=_headers(cfg),
                          params={"query": query, "locale": cfg["locale"]}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]searchAirport failed for {query}: {exc}[/yellow]")
        return None
    items = data.get("data") or []
    want = query.strip().upper()
    best = None
    for item in items:
        nav = item.get("navigation", {})
        params = nav.get("relevantFlightParams", {})
        sky = params.get("skyId")
        ent = params.get("entityId")
        if not sky or not ent:
            continue
        if str(sky).upper() == want and params.get("flightPlaceType") == "AIRPORT":
            return str(sky), str(ent)
        if best is None and (params.get("flightPlaceType") == "AIRPORT" or nav.get("entityType") == "AIRPORT"):
            best = (str(sky), str(ent))
        if best is None:
            best = (str(sky), str(ent))
    return best


def _itineraries(data: dict) -> list[dict]:
    payload = data.get("data")
    if isinstance(payload, dict):
        return payload.get("itineraries") or []
    return []


def search_one_way(cfg: dict, leg: Leg, top: int, retries: int = 4) -> list[dict]:
    """Query one-way fares for a leg via Air Scraper. Returns simplified itineraries."""
    origin = resolve_place(cfg, leg.origin)
    dest = resolve_place(cfg, leg.dest)
    if not origin or not dest:
        console.print(f"[yellow]Could not resolve skyId/entityId for {leg.origin}->{leg.dest}[/yellow]")
        return []

    url = f"https://{cfg['host']}/api/v1/flights/searchFlights"
    params = {
        "originSkyId": origin[0],
        "destinationSkyId": dest[0],
        "originEntityId": origin[1],
        "destinationEntityId": dest[1],
        "date": leg.date,
        "adults": "1",
        "sortBy": "best",
        "currency": cfg["currency"],
        "market": cfg["locale"],
        "countryCode": cfg["country"],
    }
    # The endpoint is flaky: it intermittently returns {"status": false} or an
    # "incomplete" session with zero itineraries. Retry a few times.
    data: dict = {}
    itineraries: list[dict] = []
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=_headers(cfg), params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]search failed for {leg.label} (attempt {attempt}): {exc}[/red]")
            time.sleep(2)
            continue
        itineraries = _itineraries(data)
        if itineraries:
            break
        time.sleep(2)

    if not itineraries:
        OUT.mkdir(exist_ok=True)
        dump = OUT / f"raw_leg{leg.n}.json"
        dump.write_text(json.dumps(data, indent=2))
        console.print(f"[yellow]No itineraries for {leg.label} after {retries} tries; raw saved to {dump}[/yellow]")
        return []

    results = []
    for it in itineraries:
        price = (it.get("price") or {}).get("formatted") or (it.get("price") or {}).get("raw")
        legs = it.get("legs") or []
        first = legs[0] if legs else {}
        carriers = (first.get("carriers") or {}).get("marketing") or []
        carrier = ", ".join(c.get("name", "?") for c in carriers) or "?"
        dur = first.get("durationInMinutes")
        stops = first.get("stopCount")
        results.append(
            {
                "price": price,
                "carrier": carrier,
                "duration": f"{dur // 60}h{dur % 60:02d}m" if isinstance(dur, int) else "?",
                "stops": stops if stops is not None else "?",
                "depart": (first.get("departure") or "")[11:16] or "?",
                "arrive": (first.get("arrival") or "")[5:16].replace("T", " ") or "?",
            }
        )

    def _price_key(row: dict):
        p = row["price"]
        if isinstance(p, (int, float)):
            return p
        digits = "".join(ch for ch in str(p) if ch.isdigit() or ch == ".")
        try:
            return float(digits)
        except ValueError:
            return float("inf")

    results.sort(key=_price_key)
    return results[:top]


def print_leg(leg: Leg, rows: list[dict], cfg: dict) -> None:
    table = Table(title=f"Leg {leg.n}: {leg.label}  ({leg.origin}->{leg.dest}, {leg.date})")
    table.add_column("Price", justify="right")
    table.add_column("Carrier")
    table.add_column("Depart", justify="center")
    table.add_column("Arrive", justify="center")
    table.add_column("Duration", justify="right")
    table.add_column("Stops", justify="center")
    if not rows:
        table.add_row("—", "(no data — set RAPIDAPI_KEY in .env)", "—", "—", "—", "—")
    else:
        for row in rows:
            table.add_row(str(row["price"]), row["carrier"], row.get("depart", "?"),
                          row.get("arrive", "?"), row["duration"], str(row["stops"]))
    console.print(table)


def main() -> int:
    ap = argparse.ArgumentParser(description="China 2026 trip flight search (Skyscanner via RapidAPI)")
    ap.add_argument("--leg", type=int, choices=[1, 2, 3, 4], help="query a single leg")
    ap.add_argument("--top", type=int, default=5, help="cheapest N results per leg")
    ap.add_argument("--dry-run", action="store_true", help="print legs without calling the API")
    args = ap.parse_args()

    cfg = load_config()
    legs = [l for l in LEGS if args.leg is None or l.n == args.leg]

    if args.dry_run:
        for leg in legs:
            print_leg(leg, [], cfg)
        return 0

    if not cfg["key"]:
        console.print("[yellow]No RAPIDAPI_KEY found in .env — showing planned legs only.[/yellow]")
        console.print("Add a RapidAPI Skyscanner key to .env (see .env.example) to fetch fares.\n")
        for leg in legs:
            print_leg(leg, [], cfg)
        return 0

    for leg in legs:
        rows = search_one_way(cfg, leg, args.top)
        print_leg(leg, rows, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
