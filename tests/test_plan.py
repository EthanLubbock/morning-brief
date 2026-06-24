from brief import plan


def test_load_base_has_both_variants(sandbox):
    base = plan.load_base()
    assert set(base["variants"]) == {"default", "game"}
    assert base["week_mode"] == "default"


def test_resolve_day_no_delta_returns_base(sandbox):
    base = plan.load_base()
    day = plan.resolve_day(base, "default", "monday", None)
    assert day["type"] == "gym"
    assert day["summary"] == "Squat day"


def test_resolve_day_delta_overrides(sandbox):
    base = plan.load_base()
    delta = {"summary": "Squat — moved to evening", "moved_to": "evening",
             "note": "Physio 08:00"}
    day = plan.resolve_day(base, "default", "monday", delta)
    assert day["summary"] == "Squat — moved to evening"
    assert day["note"] == "Physio 08:00"
    assert day["type"] == "gym"          # untouched base key survives


def test_resolve_day_game_variant(sandbox):
    base = plan.load_base()
    day = plan.resolve_day(base, "game", "saturday", None)
    assert day["type"] == "game"


def test_resolve_day_does_not_mutate_base(sandbox):
    base = plan.load_base()
    plan.resolve_day(base, "default", "monday", {"summary": "changed"})
    assert base["variants"]["default"]["monday"]["summary"] == "Squat day"