# Flights

James has four legs; David has two (Munich → Beijing → London). Prices are indicative economy (research only) — book direct with the airline or a trusted agent.

Tools:
- `tools/optimize_flights.py` — Amadeus-based cost optimizer (flexible-date calendar, open-jaw/multi-city comparison, good-price flag). Writes results into the Optimizer section below.
- `tools/flight_search.py` — secondary Skyscanner (RapidAPI) fare lookup.

Both need keys in `.env` (see [.env.example](.env.example)).

Status: [TODO] not booked · [HOLD] option held · [BOOKED] ticketed

# James — flights

## Leg 1 — London → Hong Kong  [TODO]
- **Route:** LHR → HKG, **direct ~12h**.
- **Target:** depart Mon 22 Jun (overnight), arrive Tue 23 Jun.
- **Carriers:** Cathay Pacific (CX), British Airways (BA), Virgin Atlantic (VS).
- **Est. economy one-way:** ~£550–£850.
- **Notes:** Cambridge → LHR via train to King's Cross + Elizabeth line/Heathrow Express, or coach (National Express A) direct from Cambridge to LHR (~2.5h). Allow 3h pre-departure.

## Leg 2 — Hong Kong → Xishuangbanna (Jinghong)  [TODO]
- **Route:** HKG → KMG (Kunming) → JHG (Jinghong). **No direct HKG–JHG flight.**
  - HKG → KMG: direct ~2h35 (China Eastern MU, Cathay, China Southern, Sichuan, Loong Air, Hong Kong Airlines).
  - KMG → JHG: direct ~1h10 (China Eastern, Lucky Air, Xiamen Air; ~55 flights/week).
- **Target:** Sat 27 Jun, **travelling with the HKU group** (Chuying to confirm exact flights).
- **Est. economy:** ~£180–£320 total (both segments).
- **Notes:** Book the two segments on one itinerary if possible, or allow a generous Kunming connection (≥2h). Mainland-China entry happens here (separate from HK) — see visa checklist.

## Leg 3 — Jinghong → Beijing  [TODO]
- **Route:** JHG → PKX (Beijing Daxing), **direct ~3h40**.
- **Target:** Sat 4 Jul.
- **Sample daily services (verify nearer the time):**
  - China Eastern MU5715 — 08:30 → 12:15
  - China Southern CZ5300 — 13:55 → 17:35
  - China Eastern MU5713 — 16:00 → 19:40
  - Beijing Capital JD5108 — evening, arrives PKX after midnight
- **Est. economy one-way:** ~£130–£220.
- **Notes:** Jinghong flights land at **Daxing (PKX)**, far south of the city. Tsinghua is in Haidian (NW Beijing) — ~1.5h+ by taxi/Daxing Express + subway. A morning flight (MU5715) maximises the arrival day.

## Leg 4 — Beijing → London  [TODO]
- **Route:** PEK/PKX → LHR, **direct ~11h**.
- **Target:** Tue 7 Jul (flexible — confirm with David / own plans).
- **Carriers:** Air China (CA, direct from PEK), British Airways (from PEK).
- **Est. economy one-way:** ~£600–£900.
- **Notes:** Prefer departing from **Capital (PEK)** — closer to Tsinghua than Daxing. Could share David's CA937 (see below).

# David Coomes — flights (economy)

David travels Munich → Beijing → London (not via ATBC). Matches his note: "arrive Wed 04:45 Air China from Munich; leave Beijing Tue 14:15".

## Leg D1 — Munich → Beijing  [TODO]
- **Route:** MUC → PEK (Beijing Capital), **direct ~9h50**, Air China **CA962**, Boeing 777-300.
- **Times:** dep ~13:00 Munich, **arr ~04:45 (+1) Beijing** — matches the stated arrival.
- **Target:** depart **Tue 30 Jun**, arrive **Wed 1 Jul** (assumption — confirm with David).
- **Est. economy one-way:** ~£350–£800 (summer peak; cheapest seen ~£440).

## Leg D2 — Beijing → London  [TODO]
- **Route:** PEK → LHR, **direct ~11h**, Air China **CA937** (best match to 14:15), 777-300.
- **Times:** dep ~14:00–14:50 Beijing, arr ~17:45 London Heathrow. (Alt: CA855 dep 12:40 or 16:30.)
- **Target:** **Tue 7 Jul**.
- **Est. economy one-way:** ~£600–£900 (Air China cheapest ~£620).
- **Notes:** Booking MUC–PEK–LHR as one **multi-city** ticket is often cheaper than two one-ways (~£1,000–£1,500 total). James could share CA937 on the return.

# Estimated flight cost summary (economy, indicative)
- **James (4 legs):** ~£1,460–£2,290.
- **David (2 legs):** ~£950–£1,700.
- See [budget.md](budget.md) for the wider expense tracker. Run `tools/optimize_flights.py --write` to replace the estimates below with live cheapest-date fares.

## Booking tracker
| Leg | Who | Date | Route | Carrier | Status | Ref | Est. price |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | James | 22 Jun | LHR→HKG | — | TODO | — | £550–850 |
| 2a | James | 27 Jun | HKG→KMG | — | TODO | — | £180–320 |
| 2b | James | 27 Jun | KMG→JHG | — | TODO | — | (incl.) |
| 3 | James | 4 Jul | JHG→PKX | — | TODO | — | £130–220 |
| 4 | James | 7 Jul | PEK→LHR | — | TODO | — | £600–900 |
| D1 | David | 30 Jun | MUC→PEK | CA962 | TODO | — | £350–800 |
| D2 | David | 7 Jul | PEK→LHR | CA937 | TODO | — | £600–900 |

## Optimizer

Live results from `tools/optimize_flights.py` land here (between the markers below). Run:

```bash
conda activate china-trip
python tools/optimize_flights.py --write            # both travellers, update this section
python tools/optimize_flights.py --traveler david --nonstop
python tools/optimize_flights.py --env production --window 3 --write
```

<!-- OPTIMIZER:START -->
_No optimizer run yet. Add Amadeus keys to `.env` and run the command above._
<!-- OPTIMIZER:END -->
