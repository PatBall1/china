#!/usr/bin/env python3
"""Flight cost optimizer for the China 2026 trip (Amadeus Self-Service API).

What it actually optimizes:
  - Flexible-date calendar search per leg (cheapest day within an allowed window).
  - Open-jaw / multi-city comparison (one ticket vs sum of one-ways) for James
    (LHR->HKG ... PEK->LHR) and David (MUC->PEK->LHR).
  - "Good price?" flag from Amadeus itinerary price metrics (fare quartiles).

Without API keys it prints the planned legs and the manual web-researched
estimates (graceful fallback), so it is always useful.

Usage:
    conda activate china-trip
    python tools/optimize_flights.py --dry-run            # no API calls
    python tools/optimize_flights.py                      # live, both travellers
    python tools/optimize_flights.py --traveler david
    python tools/optimize_flights.py --window 3 --nonstop
    python tools/optimize_flights.py --env production --write   # update flights.md
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent))
from amadeus_client import AmadeusClient, AmadeusError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FLIGHTS_MD = ROOT / "flights.md"
MARK_START = "<!-- OPTIMIZER:START -->"
MARK_END = "<!-- OPTIMIZER:END -->"
console = Console()


@dataclass
class Leg:
    code: str  # short id e.g. "J1"
    origin: str  # IATA
    dest: str  # IATA
    anchor: str  # YYYY-MM-DD target date
    window: str = "I3D"  # Amadeus dateWindow (+/- days), e.g. I3D
    est_low: float = 0.0  # manual fallback estimate (GBP)
    est_high: float = 0.0
    note: str = ""


@dataclass
class Traveller:
    name: str
    legs: list[Leg]
    # multi-city itinerary expressed as (origin, dest, anchor) hops; empty => skip
    multicity: list[tuple[str, str, str]] = field(default_factory=list)
    multicity_note: str = ""


# --- Trip configuration (edit dates/windows here) -------------------------------
TRAVELLERS = {
    "james": Traveller(
        name="James Ball",
        legs=[
            Leg("J1", "LHR", "HKG", "2026-06-22", "I2D", 550, 850,
                "Arrive HK by 23-24 Jun for workshop"),
            Leg("J2", "HKG", "JHG", "2026-06-27", "I1D", 180, 320,
                "Connects via Kunming (KMG); travel with HKU group"),
            Leg("J3", "JHG", "PKX", "2026-07-04", "I1D", 130, 220,
                "After ATBC (ends 3 Jul)"),
            Leg("J4", "PEK", "LHR", "2026-07-07", "I2D", 600, 900,
                "Return; could share David's CA937"),
        ],
        multicity=[("LHR", "HKG", "2026-06-22"), ("PEK", "LHR", "2026-07-07")],
        multicity_note="James open-jaw: LHR->HKG out, PEK->LHR back (excludes intra-China legs)",
    ),
    "david": Traveller(
        name="David Coomes",
        legs=[
            Leg("D1", "MUC", "PEK", "2026-06-30", "I2D", 350, 800,
                "Air China CA962, arr ~04:45 (+1)"),
            Leg("D2", "PEK", "LHR", "2026-07-07", "I2D", 600, 900,
                "Air China CA937, dep ~14:00-14:50"),
        ],
        multicity=[("MUC", "PEK", "2026-06-30"), ("PEK", "LHR", "2026-07-07")],
        multicity_note="David multi-city: MUC->PEK->LHR on one ticket",
    ),
}

QUARTILE_LABEL = {
    "MINIMUM": "Great",
    "FIRST": "Good",
    "MEDIUM": "Typical",
    "THIRD": "High",
    "MAXIMUM": "Very high",
}


def money(value: float | None, currency: str) -> str:
    if value is None:
        return "-"
    sym = {"GBP": "\u00a3", "EUR": "\u20ac", "USD": "$"}.get(currency, "")
    return f"{sym}{value:,.0f}"


def cheapest_by_date(offers_resp: dict) -> dict[str, float]:
    """Map departure date -> cheapest total price from a flight-offers response."""
    out: dict[str, float] = {}
    for offer in offers_resp.get("data", []) or []:
        try:
            price = float(offer["price"]["grandTotal"])
        except (KeyError, ValueError, TypeError):
            continue
        date = None
        try:
            date = offer["itineraries"][0]["segments"][0]["departure"]["at"][:10]
        except (KeyError, IndexError, TypeError):
            pass
        if not date:
            continue
        if date not in out or price < out[date]:
            out[date] = price
    return out


def offer_total(offers_resp: dict) -> float | None:
    best = None
    for offer in offers_resp.get("data", []) or []:
        try:
            price = float(offer["price"]["grandTotal"])
        except (KeyError, ValueError, TypeError):
            continue
        if best is None or price < best:
            best = price
    return best


def first_carrier(offers_resp: dict) -> str:
    try:
        offer = offers_resp["data"][0]
        code = offer["itineraries"][0]["segments"][0]["carrierCode"]
        dvy = offers_resp.get("dictionaries", {}).get("carriers", {})
        return dvy.get(code, code)
    except (KeyError, IndexError, TypeError):
        return "?"


def price_flag(client: AmadeusClient, leg: Leg, date: str, currency: str) -> str:
    try:
        resp = client.price_metrics(leg.origin, leg.dest, date, currency=currency,
                                    one_way=True, tag=f"metrics_{leg.code}")
    except AmadeusError:
        return "-"
    data = resp.get("data") or []
    if not data:
        return "-"
    metrics = data[0].get("priceMetrics", [])
    rankings = [m.get("quartileRanking") for m in metrics if m.get("quartileRanking")]
    if not rankings:
        return "-"
    # Summarise the distribution as a friendly label using the lowest band present.
    order = ["MINIMUM", "FIRST", "MEDIUM", "THIRD", "MAXIMUM"]
    present = sorted(set(rankings), key=lambda r: order.index(r) if r in order else 99)
    return QUARTILE_LABEL.get(present[0], present[0])


@dataclass
class LegResult:
    leg: Leg
    best_date: str | None = None
    best_price: float | None = None
    carrier: str = "?"
    calendar: dict[str, float] = field(default_factory=dict)
    live: bool = False
    flag: str = "-"


def optimize_leg(client: AmadeusClient | None, leg: Leg, currency: str,
                 nonstop: bool) -> LegResult:
    res = LegResult(leg=leg)
    if client is None:
        return res
    try:
        resp = client.search_offers(
            [{"originLocationCode": leg.origin, "destinationLocationCode": leg.dest,
              "departureDateTimeRange": {"date": leg.anchor, "dateWindow": leg.window}}],
            currency=currency, nonstop=nonstop, tag=f"leg_{leg.code}",
        )
    except AmadeusError as exc:
        console.print(f"[red]{leg.code} {leg.origin}->{leg.dest}: {exc}[/red]")
        return res
    if resp.get("errors"):
        detail = resp["errors"][0].get("detail", "unknown error")
        console.print(f"[yellow]{leg.code} {leg.origin}->{leg.dest}: {detail}[/yellow]")
        return res
    cal = cheapest_by_date(resp)
    if not cal:
        return res
    res.calendar = cal
    res.best_date = min(cal, key=cal.get)
    res.best_price = cal[res.best_date]
    res.carrier = first_carrier(resp)
    res.live = True
    res.flag = price_flag(client, leg, res.best_date, currency)
    return res


def optimize_multicity(client: AmadeusClient | None,
                       hops: list[tuple[str, str, str]],
                       currency: str, nonstop: bool, tag: str) -> float | None:
    if client is None or not hops:
        return None
    ods = [
        {"originLocationCode": o, "destinationLocationCode": d,
         "departureDateTimeRange": {"date": date}}
        for (o, d, date) in hops
    ]
    try:
        resp = client.search_offers(ods, currency=currency, nonstop=nonstop, tag=tag)
    except AmadeusError:
        return None
    if resp.get("errors"):
        return None
    return offer_total(resp)


def render_traveller(trav: Traveller, results: list[LegResult],
                     multicity_total: float | None, currency: str) -> Table:
    table = Table(title=f"{trav.name} - flight optimization", show_lines=False)
    table.add_column("Leg")
    table.add_column("Route")
    table.add_column("Best date")
    table.add_column("Price", justify="right")
    table.add_column("Carrier")
    table.add_column("Source")
    table.add_column("Metrics")
    for r in results:
        if r.live and r.best_price is not None:
            price = money(r.best_price, currency)
            date = r.best_date or "-"
            src = "live"
            carrier = r.carrier
        else:
            price = f"{money(r.leg.est_low, currency)}-{money(r.leg.est_high, currency)}"
            date = f"~{r.leg.anchor}"
            src = "estimate"
            carrier = "-"
        table.add_row(r.leg.code, f"{r.leg.origin}->{r.leg.dest}", date, price,
                      carrier, src, r.flag)
    # Totals
    live_sum = sum(r.best_price for r in results if r.live and r.best_price)
    est_low = sum(r.leg.est_low for r in results)
    est_high = sum(r.leg.est_high for r in results)
    if any(r.live for r in results):
        table.add_section()
        table.add_row("SUM", "(cheapest per leg, live where available)", "", money(live_sum, currency), "", "", "")
    table.add_row("EST", "(manual estimate range)", "",
                  f"{money(est_low, currency)}-{money(est_high, currency)}", "", "", "")
    if multicity_total is not None:
        table.add_section()
        table.add_row("MULTI", trav.multicity_note, "", money(multicity_total, currency),
                      "", "live", "")
    return table


def write_back(blocks: list[str]) -> None:
    if not FLIGHTS_MD.exists():
        console.print(f"[red]{FLIGHTS_MD} not found; skipping write-back.[/red]")
        return
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    content = (
        f"{MARK_START}\n\n"
        f"### Optimizer results (generated {ts})\n\n"
        + "\n\n".join(blocks)
        + f"\n\n{MARK_END}"
    )
    text = FLIGHTS_MD.read_text()
    if MARK_START in text and MARK_END in text:
        pre = text.split(MARK_START)[0]
        post = text.split(MARK_END)[1]
        text = pre + content + post
    else:
        text = text.rstrip() + "\n\n## Optimizer\n\n" + content + "\n"
    FLIGHTS_MD.write_text(text)
    console.print(f"[green]Updated {FLIGHTS_MD} optimizer section.[/green]")


def md_block(trav: Traveller, results: list[LegResult],
             multicity_total: float | None, currency: str) -> str:
    lines = [f"**{trav.name}**", "", "| Leg | Route | Best date | Price | Source |",
             "| --- | --- | --- | --- | --- |"]
    for r in results:
        if r.live and r.best_price is not None:
            price = money(r.best_price, currency)
            date = r.best_date or "-"
            src = "live"
        else:
            price = f"{money(r.leg.est_low, currency)}-{money(r.leg.est_high, currency)}"
            date = f"~{r.leg.anchor}"
            src = "estimate"
        lines.append(f"| {r.leg.code} | {r.leg.origin}->{r.leg.dest} | {date} | {price} | {src} |")
    if multicity_total is not None:
        lines.append(f"| MULTI | {trav.multicity_note} | - | {money(multicity_total, currency)} | live |")
    return "\n".join(lines)


def dump_csv(all_results: dict[str, list[LegResult]], currency: str) -> Path:
    OUT.mkdir(exist_ok=True)
    path = OUT / f"optimizer_{dt.datetime.now():%Y%m%d_%H%M%S}.csv"
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["traveller", "leg", "origin", "dest", "best_date", "price",
                    "currency", "carrier", "source", "metrics"])
        for tname, results in all_results.items():
            for r in results:
                src = "live" if r.live else "estimate"
                price = r.best_price if r.live else ""
                w.writerow([tname, r.leg.code, r.leg.origin, r.leg.dest,
                            r.best_date or r.leg.anchor, price, currency,
                            r.carrier, src, r.flag])
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="China 2026 flight cost optimizer (Amadeus)")
    ap.add_argument("--traveler", "--traveller", dest="traveler",
                    choices=["james", "david", "all"], default="all")
    ap.add_argument("--window", type=int, default=None,
                    help="override +/- date window in days (e.g. 3 -> I3D)")
    ap.add_argument("--currency", default=None, help="currency code (default from .env or GBP)")
    ap.add_argument("--nonstop", action="store_true", help="non-stop flights only")
    ap.add_argument("--env", choices=["test", "production"], default=None)
    ap.add_argument("--write", action="store_true", help="write results into flights.md")
    ap.add_argument("--dry-run", action="store_true", help="print legs, no API calls")
    args = ap.parse_args()

    currency = args.currency or os.getenv("SKYSCANNER_CURRENCY", "GBP")
    names = ["james", "david"] if args.traveler == "all" else [args.traveler]

    client: AmadeusClient | None = None
    if not args.dry_run:
        client = AmadeusClient(env=args.env)
        if not client.configured:
            console.print("[yellow]No Amadeus credentials in .env - showing estimates only.[/yellow]")
            console.print("Add AMADEUS_CLIENT_ID/SECRET to .env (see .env.example) for live optimization.\n")
            client = None
        else:
            console.print(f"[green]Amadeus {client.env} environment.[/green]\n")

    if args.window is not None:
        for trav in TRAVELLERS.values():
            for leg in trav.legs:
                leg.window = f"I{args.window}D"

    all_results: dict[str, list[LegResult]] = {}
    md_blocks: list[str] = []
    for name in names:
        trav = TRAVELLERS[name]
        results = [optimize_leg(client, leg, currency, args.nonstop) for leg in trav.legs]
        mc = optimize_multicity(client, trav.multicity, currency, args.nonstop,
                                tag=f"multicity_{name}")
        all_results[name] = results
        console.print(render_traveller(trav, results, mc, currency))
        console.print()
        md_blocks.append(md_block(trav, results, mc, currency))

    if not args.dry_run:
        csv_path = dump_csv(all_results, currency)
        console.print(f"[dim]Wrote {csv_path}[/dim]")
        if args.write:
            write_back(md_blocks)

    return 0


if __name__ == "__main__":
    sys.exit(main())
