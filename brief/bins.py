import json
from datetime import date, timedelta
from . import config


def _entries() -> list[dict]:
    return json.loads(config.BINS_FILE.read_text())


def bin_line() -> str | None:
    today = date.today()
    for e in _entries():
        d = date.fromisoformat(e["date"])
        if d == today:
            return f"Bins out tonight - {e['bin_color']}"
    return None


def expiry_warning() -> str | None:
    entries = _entries()
    if not entries:
        return "⚠ Bin schedule is empty - refresh it."
    last = max(date.fromisoformat(e["date"]) for e in entries)
    days_left = (last - date.today()).days
    if days_left <= config.BIN_EXPIRY_WARN_DAYS:
        return f"⚠ Bin schedule runs out {last.isoformat()} ({days_left}d) - refresh it."
    return None
