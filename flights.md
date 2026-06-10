# Flights

James has four legs; David has two (Munich → Beijing → London). Prices are indicative economy (research only) — book direct with the airline or a trusted agent.

Tools:
- `tools/flight_search.py` — live fare lookup via the Air Scraper API (RapidAPI). Needs `RAPIDAPI_KEY` in `.env` (see [.env.example](.env.example)). Free tier has a small monthly call cap.
- `tools/optimize_flights.py` — Amadeus cost optimizer. **Deprecated:** Amadeus is closing its Self-Service portal (decommissioned 17 Jul 2026) and has paused new signups, so this no longer works for new keys.

Status: [TODO] not booked · [HOLD] option held · [BOOKED] ticketed

Live fares below were pulled on **10 Jun 2026** (Air Scraper, economy one-way, GBP) and cross-checked with schedule data. Indicative only — confirm and book direct with the airline.

# James — flights

## Leg 1 — London → Hong Kong  [TODO]
- **Route:** LHR → HKG, **direct ~12h35**.
- **Target:** depart Mon 22 Jun (overnight), arrive Tue 23 Jun.
- **Carriers:** Cathay Pacific (CX), British Airways (BA), Virgin Atlantic (VS).
- **Live fares (22 Jun, one-way):**
  - **£620 Cathay Pacific — NONSTOP 12h35** (dep 17:00→12:35+1, or 20:15→15:45+1). _Recommended: only nonstop option; overnight, arrives early-afternoon 23 Jun._
  - £381 Etihad — 1 stop (Abu Dhabi), 16h30 (dep 09:30).
  - £384 Qatar — 1 stop (Doha), 19h30.
  - £312 Hainan — 2 stops, 28h05 (cheapest but very long).
- **Recommendation:** Cathay nonstop (~£620) for time/comfort, or Etihad 1-stop (~£381) to save ~£240 if budget matters more than the 4 extra hours.
- **Notes:** Cambridge → LHR via train to King's Cross + Elizabeth line/Heathrow Express, or coach (National Express A) direct from Cambridge to LHR (~2.5h). Allow 3h pre-departure.

## Leg 2 — Hong Kong → Xishuangbanna (Jinghong)  [TODO]
- **Route:** HKG → KMG (Kunming) → JHG (Jinghong). **No direct HKG–JHG flight.**
- **Target:** Sat 27 Jun, **travelling with the HKU group** (Chuying to confirm exact flights — this gates the final choice).
- **Live fares (27 Jun, one-way):**
  - **2a HKG → KMG (nonstop ~2h35):** £167 China Eastern **11:25→14:00** (midday; leaves room for an onward KMG→JHG hop the same day). £86 China Eastern **21:15→23:50** is cheapest but too late to connect onward.
  - **2b KMG → JHG (nonstop ~1h–1h10):** China Eastern (MU, ~42/wk), Shanghai Airlines (FM, 7/wk), Lucky Air — frequent all day, fares typically **~£50–£90**. e.g. Lucky Air 8L early, MU/FM midday & evening.
- **Recommendation:** if not locked to the group flight, take the **midday HKG→KMG (~£167)** then an **afternoon/evening KMG→JHG (~£60)** → ~**£230 total**, arriving Jinghong the evening of 27 Jun. Book both segments on **one through-ticket** if the booking site allows, otherwise allow a generous ≥2h Kunming connection.
- **Notes:** Mainland-China entry happens here (separate from HK) — see visa checklist. **Confirm the HKU group's actual flights with Chuying before ticketing.**

## Leg 3 — Jinghong → Beijing  [TODO]
- **Route:** JHG → PKX (Beijing Daxing), **direct ~3h40–3h45**.
- **Target:** Sat 4 Jul.
- **Confirmed daily nonstop services (schedule data, valid for the dates):**
  - **China Eastern MU5715 — 08:30 → 12:15 (3h45).** _Recommended: morning, maximises the Beijing arrival day._
  - China Eastern MU5713 — 16:00 → 19:40 (3h40).
  - Capital Airlines JD5108 — ~20:40/21:10 → 00:15/00:50 (+1), arrives after midnight.
- **Live fares (4 Jul, one-way):** cheapest results were 1-stop connections at **~£151–£185** (Sichuan/Xiamen, China Eastern via a hub); **nonstop** MU5715/MU5713 priced around **~£200–£275**. Worth paying for the nonstop given the long day and onward transfer.
- **Notes:** Jinghong flights land at **Daxing (PKX)**, far south of the city. Tsinghua is in Haidian (NW Beijing) — ~1.5h+ by taxi/Daxing Express + subway. The morning MU5715 gets you in by lunchtime.

## Leg 4 — Beijing → London  [TODO]
- **Route:** PEK → LHR, **direct ~11h–11h15**. Air China runs 2 nonstops/day: **CA937** and **CA855**.
- **Target:** Tue 7 Jul (flexible — confirm with David / own plans).
- **Live fares (7 Jul, one-way):**
  - **Air China CA937 — NONSTOP ~14:00 → 17:45 LHR (~11h).** _Recommended: matches David's return; depart from Capital (PEK)._ Nonstop one-way realistically **~£500–£700** in summer (route avg ~£600; cheapest seen as low as £258 off-peak).
  - £298 Emirates — 1 stop (Dubai), 18h15 (dep 07:25). Cheapest, but long.
  - £555 KLM (via AMS) / £556 Air France (via CDG) — 1 stop, ~15h30.
- **Recommendation:** **Air China CA937 nonstop**, shared with David (~£500–£700); take Emirates 1-stop (~£300) only if the ~£200–£400 saving outweighs the extra 7h.
- **Notes:** Prefer departing from **Capital (PEK)** — closer to Tsinghua than Daxing, and where Air China's nonstops + David's CA937 depart.

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
- **Live fares (7 Jul, one-way):** Air China nonstop PEK→LHR (CA937/CA855) ~£500–£700 in summer (route avg ~£600). Same flight as James's recommended Leg 4.
- **Notes:** Booking MUC–PEK–LHR as one **multi-city** ticket is often cheaper than two one-ways (~£1,000–£1,500 total). James could share CA937 on the return.

# Flight cost summary (based on live fares, 10 Jun 2026)
Using the recommended picks (nonstop where it matters):
- **James (4 legs):** Cathay LHR→HKG ~£620 + HKG→KMG→JHG ~£230 + JHG→PKX nonstop ~£230 + Air China PEK→LHR ~£600 = **~£1,680** (could trim to ~£1,200 with 1-stop long-hauls).
- **David (2 legs):** MUC→PEK ~£440 + PEK→LHR ~£600 = **~£1,040** (or a multi-city MUC–PEK–LHR ticket ~£1,000–£1,500).
- See [budget.md](budget.md) for the wider expense tracker.

## Booking tracker
| Leg | Who | Date | Route | Recommended | Status | Ref | Live price |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | James | 22 Jun | LHR→HKG | Cathay Pacific (nonstop, 17:00/20:15) | TODO | — | ~£620 |
| 2a | James | 27 Jun | HKG→KMG | China Eastern 11:25→14:00 (nonstop) | TODO | — | ~£167 |
| 2b | James | 27 Jun | KMG→JHG | China Eastern / Lucky Air (nonstop ~1h) | TODO | — | ~£60 |
| 3 | James | 4 Jul | JHG→PKX | China Eastern MU5715 08:30→12:15 (nonstop) | TODO | — | ~£230 |
| 4 | James | 7 Jul | PEK→LHR | Air China CA937 (nonstop, ~14:00) | TODO | — | ~£600 |
| D1 | David | 30 Jun | MUC→PEK | Air China CA962 (nonstop) | TODO | — | ~£440 |
| D2 | David | 7 Jul | PEK→LHR | Air China CA937 (nonstop, with James) | TODO | — | ~£600 |

## Fare source

Live fares pulled with `tools/flight_search.py` (Air Scraper / RapidAPI) on 10 Jun 2026, cross-checked against published schedules. Re-run to refresh (free tier has a small monthly quota, so space out runs):

```bash
conda activate china-trip
python tools/flight_search.py --top 6        # all legs
python tools/flight_search.py --leg 4        # single leg
```
