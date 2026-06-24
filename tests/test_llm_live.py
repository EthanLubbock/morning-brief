"""Live tests — real OpenAI calls. Run with: pytest -m live

These cost fractions of a penny each. They assert structure, not exact
strings, because even at temperature 0 the model isn't byte-deterministic.
"""
import os

import pytest

from brief import llm

pytestmark = pytest.mark.live

_NEEDS_KEY = pytest.mark.skipif(
    os.environ.get("OPENAI_API_KEY", "placeholder") == "placeholder",
    reason="real OPENAI_API_KEY not set")


def _find(intents, action):
    return [i for i in intents if i.get("action") == action]


@_NEEDS_KEY
def test_parse_add_todo():
    intents = llm.parse_email("Add: buy wedding flowers, high priority")
    adds = _find(intents, "add_todo")
    assert adds, f"expected an add_todo, got {intents}"
    assert "flower" in adds[0].get("title", "").lower()


@_NEEDS_KEY
def test_parse_constraint():
    intents = llm.parse_email("Can't get up early Thursday, dentist at 8")
    cons = _find(intents, "add_constraint")
    assert cons, f"expected an add_constraint, got {intents}"
    assert "thursday" in cons[0].get("applies_to", [])


@_NEEDS_KEY
def test_parse_game_week():
    intents = llm.parse_email("I'll be playing hockey this Saturday")
    modes = _find(intents, "set_week_mode")
    assert modes, f"expected set_week_mode, got {intents}"
    assert modes[0].get("mode") == "game"


@_NEEDS_KEY
def test_parse_complete_todo():
    intents = llm.parse_email("Done with chasing the ring sizing")
    comp = _find(intents, "complete_todo")
    assert comp, f"expected complete_todo, got {intents}"
    assert "ring" in comp[0].get("match", "").lower()


@_NEEDS_KEY
def test_parse_empty_on_smalltalk():
    intents = llm.parse_email("Morning! Hope you're well, no changes today.")
    assert intents == [] or all(
        i["action"] not in {"add_todo", "add_constraint", "set_week_mode"}
        for i in intents)


@_NEEDS_KEY
def test_parse_compound_email():
    intents = llm.parse_email(
        "Can't do Wednesday morning (physio at 8), and add: post wedding RSVPs")
    assert _find(intents, "add_constraint")
    assert _find(intents, "add_todo")


@_NEEDS_KEY
def test_replan_returns_days_and_rationale(sandbox, monkeypatch):
    # keep this about the LLM, not iCloud: stub the calendar fetch
    monkeypatch.setattr(llm, "calendar_feed",
                        type("C", (), {"upcoming_events": staticmethod(lambda d=7: [])}))
    from brief import plan
    base = plan.load_base()
    state_data = {
        "week_mode": "default",
        "constraints": [{"raw": "no Wednesday morning, physio",
                         "applies_to": ["wednesday"], "reason": "physio",
                         "persist": False, "received": "x"}],
    }
    days, rationale = llm.replan_week(base, state_data)
    assert isinstance(days, dict)
    assert isinstance(rationale, str) and rationale