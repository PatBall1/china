# China Trip 2026 — Planning Workspace

Planning hub for James Ball's June–July 2026 trip: **Hong Kong (pre-ATBC workshop) → Xishuangbanna (ATBC 2026) → Beijing (Tsinghua visit)**.

## Trip at a glance

| Leg | Where | Dates | Purpose |
| --- | --- | --- | --- |
| 1 | Hong Kong | 23–27 Jun | Pre-ATBC mini-workshop (HKU); keynote AM 26 Jun |
| 2 | Xishuangbanna (Jinghong) | 27 Jun – 4 Jul | ATBC 2026 (62nd annual meeting) |
| 3 | Beijing | 4–7 Jul | Tsinghua visit with David Coomes (host: Le Yu) |

Dates above are the **working plan** — see [itinerary.md](itinerary.md) for detail and open questions.

## How to use this workspace

- [itinerary.md](itinerary.md) — master day-by-day plan.
- [flights.md](flights.md) — flight legs, researched options, booking status.
- [accommodation.md](accommodation.md) — hotels per city, who pays, deadlines.
- [contacts.md](contacts.md) — everyone involved + emails/phones.
- [budget.md](budget.md) — funding sources and expense tracker.
- `schedule/` — per-city detailed schedules.
- `talks/` — talk titles, abstracts, slides notes.
- `emails/` — draft replies ready to send.
- `checklists/` — deadlines + pre-trip (visa, insurance, packing).
- `tools/optimize_flights.py` — Amadeus cost optimizer (flexible-date, multi-city, good-price flag).
- `tools/flight_search.py` — secondary Skyscanner (RapidAPI) fare lookup.
- `correspondence/` — source emails this plan is built from.

## Status dashboard

- [ ] **URGENT (10 Jun):** book ATBC conference hotel (Mekong River Jing Land) — see [accommodation.md](accommodation.md).
- [ ] Reply to Chuying: HK arrival/departure dates + keynote title — [emails/draft-chuying-reply.md](emails/draft-chuying-reply.md).
- [ ] Confirm Beijing window with David; ask Le Yu for hotel — [emails/draft-leyu-reply.md](emails/draft-leyu-reply.md).
- [ ] Book 4 flight legs — [flights.md](flights.md).
- [ ] Verify China visa/entry for UK passport — [checklists/pre-trip.md](checklists/pre-trip.md).

## Python environment

Created with Miniforge. Activate with:

```bash
conda activate china-trip
```

Env spec lives in [environment.yml](environment.yml). To recreate:

```bash
mamba env create -f environment.yml
```

## Flight cost optimization

`tools/optimize_flights.py` uses the **Amadeus Self-Service API** to actually optimize cost:
- flexible-date calendar search (cheapest day within each leg's allowed window),
- open-jaw / multi-city comparison (one ticket vs separate one-ways) for James and David,
- a "good price?" flag from Amadeus fare-quartile metrics.

Setup:
1. Create a free app at [developers.amadeus.com](https://developers.amadeus.com) → copy the API Key + Secret.
2. `cp .env.example .env` and set `AMADEUS_CLIENT_ID` / `AMADEUS_CLIENT_SECRET` (and `AMADEUS_ENV=test` or `production`).
3. Run it:

```bash
conda activate china-trip
python tools/optimize_flights.py --dry-run          # no key needed; shows legs + estimates
python tools/optimize_flights.py                    # live, both travellers
python tools/optimize_flights.py --env production --window 3 --write   # update flights.md
```

Without keys it gracefully prints the planned legs and manual estimates. Results (and a CSV in `out/`) are written into the Optimizer section of [flights.md](flights.md). Secrets in `.env` are gitignored.
