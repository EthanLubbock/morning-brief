from datetime import date

import pytest

from brief import calendar_feed, config


def _ics_for(day: date, summary: str = "Dentist", hour: str = "08") -> bytes:
    stamp = day.strftime("%Y%m%d")
    return (f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//t//t//EN\n"
            f"BEGIN:VEVENT\nUID:1@t\nDTSTART:{stamp}T{hour}0000Z\n"
            f"DTEND:{stamp}T{hour}3000Z\nSUMMARY:{summary}\nEND:VEVENT\n"
            f"END:VCALENDAR").encode()


class _Resp:
    def __init__(self, content): self.content = content


@pytest.fixture
def two_calendars(monkeypatch):
    monkeypatch.setattr(config, "CALENDARS", [
        {"name": "Ethan",  "role": "mine",   "url": "https://x/ethan.ics"},
        {"name": "Shared", "role": "shared", "url": "https://x/shared.ics"},
    ])


def test_todays_event_is_returned(two_calendars, monkeypatch):
    # regression: a [today, today] window returned nothing; must be [today, tomorrow)
    ics = _ics_for(date.today())
    monkeypatch.setattr(calendar_feed.requests, "get", lambda *a, **k: _Resp(ics))
    events = calendar_feed.todays_events()
    assert any(e["title"] == "Dentist" for e in events)


def test_dedupe_across_calendars(two_calendars, monkeypatch):
    ics = _ics_for(date.today())                     # same event on both feeds
    monkeypatch.setattr(calendar_feed.requests, "get", lambda *a, **k: _Resp(ics))
    events = [e for e in calendar_feed.todays_events() if e["role"] != "error"]
    assert len(events) == 1                          # joint event collapsed to one


def test_role_is_tagged(two_calendars, monkeypatch):
    def fake_get(url, **k):
        return _Resp(_ics_for(date.today(),
                              summary="Mine" if "ethan" in url else "Theirs"))
    monkeypatch.setattr(calendar_feed.requests, "get", fake_get)
    by_title = {e["title"]: e for e in calendar_feed.todays_events()}
    assert by_title["Mine"]["role"] == "mine"
    assert by_title["Theirs"]["role"] == "shared"


def test_unreachable_calendar_degrades(two_calendars, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("iCloud down")
    monkeypatch.setattr(calendar_feed.requests, "get", boom)
    events = calendar_feed.todays_events()
    assert len(events) == 2                           # one error line per calendar
    assert all(e["role"] == "error" for e in events)  # brief still builds