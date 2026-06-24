import logging
import requests
import icalendar
import recurring_ical_events
from datetime import date, datetime, timedelta
from . import config

log = logging.getLogger("brief.calendar")


def _occurrences(cal, start: date, end: date) -> list:
    """Events whose start falls in [start, end). Library first, manual fallback."""
    start_dt = datetime(start.year, start.month, start.day)
    end_dt = datetime(end.year, end.month, end.day)
    try:
        evs = list(recurring_ical_events.of(cal).between(start_dt, end_dt))
        if evs:
            return evs
    except Exception:
        log.exception("recurring_ical_events failed; using manual fallback")
    out = []                                          # fallback: non-recurring events
    for comp in cal.walk("VEVENT"):
        if comp.get("RRULE"):                         # recurring needs the library; skip
            continue
        dt = comp["DTSTART"].dt
        day = dt.date() if isinstance(dt, datetime) else dt
        if start <= day < end:
            out.append(comp)
    return out


def _events_in_range(start: date, end: date) -> list[dict]:
    """Events in [start, end) - end exclusive."""
    out, seen = [], set()
    for cal_cfg in config.CALENDARS:
        if not cal_cfg["url"]:
            continue
        try:
            ics = requests.get(cal_cfg["url"], timeout=15).content
            cal = icalendar.Calendar.from_ical(ics)
            for e in _occurrences(cal, start, end):
                dt = e["DTSTART"].dt
                is_dt = isinstance(dt, datetime)
                day = dt.date() if is_dt else dt
                t = dt.strftime("%H:%M") if is_dt else "all day"
                title = str(e.get("SUMMARY", ""))
                key = (day.isoformat(), t, title.lower())
                if key in seen:                       # event on both calendars
                    continue
                seen.add(key)
                out.append({"date": day.isoformat(), "time": t, "title": title,
                            "cal": cal_cfg["name"], "role": cal_cfg["role"]})
        except Exception:
            log.exception("calendar %s failed", cal_cfg["name"])
            out.append({"date": start.isoformat(), "time": "", "role": "error",
                        "title": f"({cal_cfg['name']} calendar unavailable)",
                        "cal": cal_cfg["name"]})
    return sorted(out, key=lambda x: (x["date"], x["time"]))


def todays_events() -> list[dict]:
    today = date.today()                              # end-exclusive: [today, tomorrow)
    return _events_in_range(today, today + timedelta(days=1))


def upcoming_events(days: int = 7) -> list[dict]:
    today = date.today()
    return _events_in_range(today, today + timedelta(days=days))