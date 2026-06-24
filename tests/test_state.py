from datetime import date, timedelta

from brief.state import WeekState, _monday_of


def test_fresh_state_defaults(sandbox):
    state = WeekState.load()
    assert state.data["week_mode"] == "default"
    assert state.data["constraints"] == []
    assert state.data["days"] == {}


def test_add_constraint_flags_replan(sandbox):
    state = WeekState.load()
    needs = state.apply_intents([{
        "action": "add_constraint", "constraint": "no early thursday",
        "applies_to": ["thursday"], "reason": "dentist", "persist": False}])
    assert needs is True
    assert len(state.data["constraints"]) == 1
    assert state.data["constraints"][0]["raw"] == "no early thursday"
    assert state.data["constraints"][0]["applies_to"] == ["thursday"]


def test_set_week_mode_switches_and_clears_days(sandbox):
    state = WeekState.load()
    state.data["days"] = {"monday": {"note": "stale"}}
    needs = state.apply_intents([{
        "action": "set_week_mode", "mode": "game", "game_day": "saturday"}])
    assert needs is True
    assert state.data["week_mode"] == "game"
    assert state.data["days"] == {}             # variant change wipes deltas


def test_add_todo_intent_does_not_trigger_replan(sandbox):
    # todo intents are handled by inbox/TodoStore, not the schedule
    state = WeekState.load()
    needs = state.apply_intents([{"action": "add_todo", "title": "x"}])
    assert needs is False


def test_persist_flag_sets_all_constraints(sandbox):
    state = WeekState.load()
    state.apply_intents([{"action": "add_constraint", "constraint": "evenings",
                          "applies_to": ["thursday"], "persist": False}])
    state.apply_intents([{"action": "persist_current_changes"}])
    assert state.data["constraints"][0]["persist"] is True


def test_weekly_reset_drops_nonpersisted(sandbox):
    state = WeekState.load()
    state.apply_intents([{"action": "add_constraint", "constraint": "one-off",
                          "applies_to": ["monday"], "persist": False}])
    state.set_days({"monday": {"note": "x"}}, "rationale")
    state.weekly_reset()
    assert state.data["constraints"] == []
    assert state.data["days"] == {}


def test_weekly_reset_keeps_persisted_verbatim(sandbox):
    state = WeekState.load()
    state.apply_intents([{"action": "add_constraint", "constraint": "keep evenings",
                          "applies_to": ["thursday"], "persist": True}])
    state.weekly_reset()
    assert len(state.data["constraints"]) == 1
    # the bug we fixed: raw text must survive the reset, not become ""
    assert state.data["constraints"][0]["raw"] == "keep evenings"
    assert state.data["constraints"][0]["applies_to"] == ["thursday"]


def test_reset_week_intent(sandbox):
    state = WeekState.load()
    state.apply_intents([{"action": "add_constraint", "constraint": "x",
                          "applies_to": ["monday"], "persist": False}])
    state.apply_intents([{"action": "reset_week"}])
    assert state.data["constraints"] == []


def test_save_and_reload_roundtrip(sandbox):
    state = WeekState.load()
    state.set_days({"friday": {"note": "physio"}}, "moved friday")
    state.save()
    reloaded = WeekState.load()
    assert reloaded.data["days"]["friday"]["note"] == "physio"
    assert reloaded.data["replan_rationale"] == "moved friday"


def test_stale_week_rebuilds_fresh(sandbox):
    old_monday = (_monday_of(date.today()) - timedelta(days=14)).isoformat()
    sandbox.write_week_state({
        "week_of": old_monday, "week_mode": "game", "game_day": "saturday",
        "constraints": [{"raw": "old", "applies_to": ["monday"], "persist": False,
                         "reason": "", "received": "x"}],
        "days": {"monday": {"note": "old"}}, "replan_rationale": "old"})
    state = WeekState.load()
    assert state.data["week_of"] == _monday_of(date.today()).isoformat()
    assert state.data["week_mode"] == "default"   # rebuilt from base
    assert state.data["days"] == {}


def test_current_week_loads_as_is(sandbox):
    this_monday = _monday_of(date.today()).isoformat()
    sandbox.write_week_state({
        "week_of": this_monday, "week_mode": "game", "game_day": "saturday",
        "constraints": [], "days": {"monday": {"note": "keep me"}},
        "replan_rationale": "r"})
    state = WeekState.load()
    assert state.data["week_mode"] == "game"
    assert state.data["days"]["monday"]["note"] == "keep me"