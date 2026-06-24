import json
import os
from datetime import date, timedelta

import pytest
from dotenv import load_dotenv

# Pull real .env first so live tests get real secrets; placeholders only
# fill gaps so the package imports when secrets are absent (real values win).
load_dotenv()
os.environ.setdefault("OWNER_EMAIL", "elubbock@gmail.com")
os.environ.setdefault("GMAIL_USER", "bot@gmail.com")
os.environ.setdefault("GMAIL_APP_PASSWORD", "placeholder")
os.environ.setdefault("OPENAI_API_KEY", "placeholder")

from brief import config  # noqa: E402

ISO = lambda d: d.isoformat()
TODAY = date.today()

BASE_PLAN_YAML = """
timezone: Europe/London
week_mode: default
game_day: saturday
daily: "Steps 8-10k."
variants:
  default:
    monday: {type: gym, summary: "Squat day"}
    tuesday: {type: run, summary: "Easy run"}
    wednesday: {type: gym, summary: "Deadlift day"}
    thursday: {type: run, summary: "Easy run"}
    friday: {type: gym, summary: "Bench day"}
    saturday: {type: run_optional, summary: "Optional run"}
    sunday: {type: rest, summary: "Rest"}
  game:
    monday: {type: gym, summary: "Squat day"}
    tuesday: {type: rest, summary: "Rest"}
    wednesday: {type: gym, summary: "Deadlift day"}
    thursday: {type: rest, summary: "Rest"}
    friday: {type: gym, summary: "Bench day"}
    saturday: {type: game, summary: "GAME"}
    sunday: {type: rest, summary: "Rest"}
replan_rules: ["Drop the run not the lift."]
recurring_tasks: []
"""

DEFAULT_TODOS = {
    "tasks": [
        {"id": "t-001", "title": "high no due", "priority": "high",
         "added": ISO(TODAY - timedelta(days=1)), "due": None, "done": False},
        {"id": "t-002", "title": "medium soon", "priority": "medium",
         "added": ISO(TODAY), "due": ISO(TODAY + timedelta(days=3)), "done": False},
        {"id": "t-003", "title": "low old", "priority": "low",
         "added": ISO(TODAY - timedelta(days=40)), "due": None, "done": False},
        {"id": "t-004", "title": "done already", "priority": "high",
         "added": ISO(TODAY), "due": None, "done": True},
    ]
}


class Sandbox:
    """Writes test data into the monkeypatched config paths."""

    def write_todos(self, data: dict) -> None:
        config.TODOS_FILE.write_text(json.dumps(data))

    def write_bins(self, entries: list) -> None:
        config.BINS_FILE.write_text(json.dumps(entries))

    def write_week_state(self, data: dict) -> None:
        config.WEEK_STATE_FILE.write_text(json.dumps(data))


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    base = tmp_path / "base_plan.yaml"
    base.write_text(BASE_PLAN_YAML)

    monkeypatch.setattr(config, "BASE_PLAN_FILE", base)
    monkeypatch.setattr(config, "DATA", data)
    monkeypatch.setattr(config, "TODOS_FILE", data / "todos.json")
    monkeypatch.setattr(config, "BINS_FILE", data / "bins.json")
    monkeypatch.setattr(config, "WEEK_STATE_FILE", data / "week_state.json")

    sb = Sandbox()
    sb.write_todos(DEFAULT_TODOS)
    sb.write_bins([])
    return sb