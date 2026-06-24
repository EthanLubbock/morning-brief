from datetime import date

from brief import morning


def _stub_calendar(monkeypatch, events):
    monkeypatch.setattr(morning.calendar_feed, "todays_events", lambda: events)


def test_brief_contains_workout_and_tasks(sandbox, monkeypatch):
    _stub_calendar(monkeypatch, [])
    subject, body = morning.build_brief()
    day = ["monday", "tuesday", "wednesday", "thursday",
           "friday", "saturday", "sunday"][date.today().weekday()]
    expected = {"monday": "Squat", "tuesday": "Easy run", "wednesday": "Deadlift",
                "thursday": "Easy run", "friday": "Bench", "saturday": "Optional",
                "sunday": "Rest"}[day]
    assert expected in body
    assert "WORKOUT" in body
    assert "TASKS" in body
    assert "Steps 8-10k." in body            # daily line
    assert "Resets Sunday night." in body


def test_brief_renders_calendar_with_shared_tag(sandbox, monkeypatch):
    _stub_calendar(monkeypatch, [
        {"time": "08:00", "title": "Dentist", "cal": "Ethan", "role": "mine"},
        {"time": "18:30", "title": "Dinner", "cal": "Shared", "role": "shared"},
    ])
    _, body = morning.build_brief()
    assert "Dentist" in body
    assert "Dinner" in body
    assert "[shared]" in body


def test_brief_includes_bin_line(sandbox, monkeypatch):
    _stub_calendar(monkeypatch, [])
    sandbox.write_bins([{"date": date.today().isoformat(), "bin": "blue"}])
    _, body = morning.build_brief()
    assert "Bin collection today — blue" in body


def test_subject_reflects_task_count(sandbox, monkeypatch):
    _stub_calendar(monkeypatch, [])
    subject, _ = morning.build_brief()
    assert "3 tasks" in subject


def test_game_mode_shows_in_footer(sandbox, monkeypatch):
    _stub_calendar(monkeypatch, [])
    from brief.state import WeekState
    state = WeekState.load()
    state.apply_intents([{"action": "set_week_mode", "mode": "game",
                          "game_day": "saturday"}])
    state.save()
    _, body = morning.build_brief()
    assert "GAME week" in body