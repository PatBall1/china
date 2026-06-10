#!/usr/bin/env python3
"""Flight fare lookup for the China 2026 trip, via a Skyscanner endpoint on RapidAPI.

Skyscanner's official API is partner-only, so this targets a community Skyscanner
endpoint on RapidAPI (default host: sky-scanner3.p.rapidapi.com). Provide a key in
.env (see .env.example). Without a key the script still prints the planned legs.

Usage:
    conda activate china-trip
    python tools/flight_search.py            # query every leg
    python tools/flight_search.py --leg 1    # query a single leg (1-4)
    python tools/flight_search.py --top 5    # show top N cheapest per leg
    python tools/flight_search.py --dry-run  # just print the legs, no API call

Notes:
- Fares are indicative for comparison only; book directly with the airline.
- Different RapidAPI Skyscanner providers use slightly different schemas. This
  script parses the common sky-scanner3 shape defensively and saves raw JSON to
  out/ when it can't interpret a response, so you can adapt the parser.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
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
        "host": os.getenv("RAPIDAPI_SKYSCANNER_HOST", "sky-scanner3.p.rapidapi.com"),
        "market": os.getenv("SKYSCANNER_MARKET", "UK"),
        "currency": os.getenv("SKYSCANNER_CURRENCY", "GBP"),
        "locale": os.getenv("SKYSCANNER_LOCALE", "en-GB"),
    }


def _headers(cfg: dict) -> dict:
    return {"x-rapidapi-key": cfg["key"], "x-rapidapi-host": cfg["host"]}


def resolve_entity(cfg: dict, query: str) -> str | None:
    """Resolve an IATA code / place name to a Skyscanner entityId via auto-complete."""
    url = f"https://{cfg['host']}/flights/auto-complete"
    try:
        r = requests.get(url, headers=_headers(cfg), params={"query": query}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]auto-complete failed for {query}: {exc}[/yellow]")
        return None
    items = data.get("data") or data.get("places") or []
    for item in items:
        pres = item.get("presentation", {})
        nav = item.get("navigation", {}).get("relevantFlightParams", {})
        ent = nav.get("entityId") or pres.get("id") or item.get("entityId")
        if ent:
            return str(ent)
    return None


def search_one_way(cfg: dict, leg: Leg, top: int) -> list[dict]:
    """Query one-way fares for a leg. Returns a list of simplified itineraries."""
    origin_id = resolve_entity(cfg, leg.origin)
    dest_id = resolve_entity(cfg, leg.dest)
    if not origin_id or not dest_id:
        console.print(f"[yellow]Could not resolve entity ids for {leg.origin}->{leg.dest}[/yellow]")
        return []

    url = f"https://{cfg['host']}/flights/search-one-way"
    params = {
        "fromEntityId": origin_id,
        "toEntityId": dest_id,
        "departDate": leg.date,
        "market": cfg["market"],
        "currency": cfg["currency"],
        "locale": cfg["locale"],
    }
    try:
        r = requests.get(url, headers=_headers(cfg), params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]search failed for {leg.label}: {exc}[/red]")
        return []

    itineraries = (data.get("data") or {}).get("itineraries") or []
    if not itineraries:
        OUT.mkdir(exist_ok=True)
        dump = OUT / f"raw_leg{leg.n}.json"
        dump.write_text(json.dumps(data, indent=2))
        console.print(f"[yellow]No itineraries parsed; raw response saved to {dump}[/yellow]")
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
    table.add_column("Duration", justify="right")
    table.add_column("Stops", justify="center")
    if not rows:
        table.add_row("—", "(no data — set RAPIDAPI_KEY in .env)", "—", "—")
    else:
        for row in rows:
            table.add_row(str(row["price"]), row["carrier"], row["duration"], str(row["stops"]))
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
