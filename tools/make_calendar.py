#!/usr/bin/env python3
"""Generate provisional .ics calendars for James and David (China 2026 trip).

Produces calendar/james.ics and calendar/david.ics, importable into Google /
Outlook / Apple Calendar. All-day events use plain dates; flights and the
keynote use local times with proper time zones. Everything is marked
provisional in the event description.

Usage:
    conda activate china-trip
    python tools/make_calendar.py
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

ROOT = Path(__file__).resolve().parent.parent
CAL_DIR = ROOT / "calendar"

LONDON = ZoneInfo("Europe/London")
BERLIN = ZoneInfo("Europe/Berlin")
CHINA = ZoneInfo("Asia/Shanghai")  # mainland + HK share UTC+8
PROVISIONAL = "Provisional - subject to confirmation (flights unbooked)."


@dataclass
class Ev:
    summary: str
    start: dt.date | dt.datetime
    end: dt.date | dt.datetime
    location: str = ""
    desc: str = ""


def _james_events() -> list[Ev]:
    return [
        Ev("\u2708 LHR \u2192 Hong Kong (overnight)",
           dt.datetime(2026, 6, 22, 21, 0, tzinfo=LONDON),
           dt.datetime(2026, 6, 23, 16, 45, tzinfo=CHINA),
           "London Heathrow \u2192 HKG", "Direct ~12h. Provisional time."),
        Ev("Check in \u2014 JEN Hotel (HKU)", dt.date(2026, 6, 23), dt.date(2026, 6, 24),
           "JEN Hotel, Hong Kong", "HKU-covered, 5 min from campus."),
        Ev("\u25cf HK pre-ATBC workshop \u2014 Day 1", dt.date(2026, 6, 24), dt.date(2026, 6, 25),
           "HKU", ""),
        Ev("\u25cf HK pre-ATBC workshop \u2014 Day 2", dt.date(2026, 6, 25), dt.date(2026, 6, 26),
           "HKU", ""),
        Ev("\u2605 Keynote \u2014 Frontiers in RS & AI in Ecology",
           dt.datetime(2026, 6, 26, 9, 30, tzinfo=CHINA),
           dt.datetime(2026, 6, 26, 10, 0, tzinfo=CHINA),
           "HKU", "17 min talk + 3 min Q&A. Morning session."),
        Ev("\u2708 HKG \u2192 Jinghong (via Kunming) w/ HKU group",
           dt.date(2026, 6, 27), dt.date(2026, 6, 28),
           "HKG \u2192 KMG \u2192 JHG", "No direct flight; connect in Kunming."),
        Ev("\u25cf ATBC 2026 \u2014 registration + opening", dt.date(2026, 6, 28), dt.date(2026, 6, 29),
           "Mekong River Jing Land Hotel, Jinghong", ""),
        Ev("\u25cf ATBC 2026 \u2014 sessions", dt.date(2026, 6, 29), dt.date(2026, 7, 3),
           "Jinghong, Xishuangbanna", "Keynotes, symposia, posters."),
        Ev("\u25cf ATBC 2026 \u2014 field trips", dt.date(2026, 7, 3), dt.date(2026, 7, 4),
           "Xishuangbanna", ""),
        Ev("\u2708 Jinghong \u2192 Beijing (PKX)",
           dt.datetime(2026, 7, 4, 8, 30, tzinfo=CHINA),
           dt.datetime(2026, 7, 4, 12, 15, tzinfo=CHINA),
           "JHG \u2192 PKX", "e.g. MU5715. Transfer to Haidian (~1.5h)."),
        Ev("\u25cb Beijing \u2014 prep / free", dt.date(2026, 7, 5), dt.date(2026, 7, 6),
           "Beijing", ""),
        Ev("\u2605 Tsinghua \u2014 informal talk + Le Yu",
           dt.date(2026, 7, 6), dt.date(2026, 7, 7),
           "Tsinghua University, Haidian", "Share draft manuscript; Tessera plans."),
        Ev("\u2708 Beijing \u2192 London",
           dt.datetime(2026, 7, 7, 14, 0, tzinfo=CHINA),
           dt.datetime(2026, 7, 7, 17, 45, tzinfo=LONDON),
           "PEK \u2192 LHR", "Could share David's CA937. Provisional."),
    ]


def _david_events() -> list[Ev]:
    return [
        Ev("\u2708 Munich \u2192 Beijing (CA962)",
           dt.datetime(2026, 6, 30, 13, 0, tzinfo=BERLIN),
           dt.datetime(2026, 7, 1, 4, 45, tzinfo=CHINA),
           "MUC \u2192 PEK", "Air China CA962, Boeing 777-300, ~9h50."),
        Ev("Check in \u2014 Beijing hotel (near Tsinghua)", dt.date(2026, 7, 1), dt.date(2026, 7, 2),
           "Haidian, Beijing", "Hotel recommendation pending from Le Yu."),
        Ev("\u25cb Peking University (tentative)", dt.date(2026, 7, 2), dt.date(2026, 7, 3),
           "Peking University", "Not yet organised."),
        Ev("\u2605 Tsinghua \u2014 David's talk + Le Yu",
           dt.date(2026, 7, 3), dt.date(2026, 7, 4),
           "Tsinghua University, Haidian", "Talk + conversation with students/staff."),
        Ev("\u25cb Weekend (James arrives after ATBC)", dt.date(2026, 7, 4), dt.date(2026, 7, 6),
           "Beijing", ""),
        Ev("\u25cf Tsinghua \u2014 more time with Le Yu", dt.date(2026, 7, 6), dt.date(2026, 7, 7),
           "Tsinghua University, Haidian", "James's informal talk."),
        Ev("\u2708 Beijing \u2192 London (CA937)",
           dt.datetime(2026, 7, 7, 14, 0, tzinfo=CHINA),
           dt.datetime(2026, 7, 7, 17, 45, tzinfo=LONDON),
           "PEK \u2192 LHR", "Air China CA937, ~11h. Provisional time."),
    ]


def build_calendar(name: str, events: list[Ev]) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//china-trip//provisional calendar//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", f"China 2026 \u2014 {name}")
    stamp = dt.datetime.now(tz=dt.timezone.utc)
    slug = name.lower().split()[0]
    for i, ev in enumerate(events):
        item = Event()
        item.add("summary", ev.summary)
        item.add("dtstart", ev.start)
        item.add("dtend", ev.end)
        if ev.location:
            item.add("location", ev.location)
        desc = (ev.desc + "\n\n" if ev.desc else "") + PROVISIONAL
        item.add("description", desc)
        item.add("dtstamp", stamp)
        item.add("uid", f"china2026-{slug}-{i:02d}@patball1.github.io")
        cal.add_component(item)
    return cal


def main() -> int:
    CAL_DIR.mkdir(exist_ok=True)
    for name, events in (("James", _james_events()), ("David", _david_events())):
        cal = build_calendar(name, events)
        path = CAL_DIR / f"{name.lower()}.ics"
        path.write_bytes(cal.to_ical())
        print(f"Wrote {path} ({len(events)} events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
