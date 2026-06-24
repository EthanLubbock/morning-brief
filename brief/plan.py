import yaml
from . import config


def load_base() -> dict:
    with open(config.BASE_PLAN_FILE) as f:
        return yaml.safe_load(f)


def resolve_day(base: dict, week_mode: str, day: str, delta: dict | None) -> dict:
    """Return the effective session for `day`: base variant + any delta."""
    session = dict(base["variants"][week_mode][day])   # copy
    if delta:
        session.update(delta)                          # delta overrides keys
    return session