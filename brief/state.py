import json
from datetime import date, datetime, timedelta
from . import config, plan


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


class WeekState:
    def __init__(self, data: dict):
        self.data = data

    # ---- construction -------------------------------------------------
    @classmethod
    def load(cls) -> "WeekState":
        base = plan.load_base()
        this_monday = _monday_of(date.today()).isoformat()
        if config.WEEK_STATE_FILE.exists():
            data = json.loads(config.WEEK_STATE_FILE.read_text())
            if data.get("week_of") == this_monday:
                return cls(data)
        return cls.fresh(base, this_monday)            # missing or stale → rebuild

    @classmethod
    def fresh(cls, base: dict, week_of: str,
              carry_constraints: list | None = None) -> "WeekState":
        return cls({
            "week_of": week_of,
            "week_mode": base.get("week_mode", "default"),
            "game_day": base.get("game_day", "saturday"),
            "constraints": carry_constraints or [],
            "days": {},                                # only changed days live here
            "replan_rationale": "",
        })

    # ---- persistence --------------------------------------------------
    def save(self) -> None:
        config.WEEK_STATE_FILE.parent.mkdir(exist_ok=True)
        tmp = config.WEEK_STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2))
        tmp.replace(config.WEEK_STATE_FILE)            # atomic, SD-card safe

    # ---- mutation (called by inbox.py) --------------------------------
    def apply_intents(self, intents: list[dict]) -> bool:
        """Returns True if a replan is needed (schedule actually changed)."""
        needs_replan = False
        for it in intents:
            action = it.get("action")
            if action == "add_constraint":
                self.data["constraints"].append({
                    "raw": it.get("constraint", ""),
                    "applies_to": it.get("applies_to", []),
                    "reason": it.get("reason", ""),
                    "persist": bool(it.get("persist", False)),
                    "received": datetime.now().isoformat(timespec="seconds"),
                })
                needs_replan = True
            elif action == "set_week_mode":
                self.data["week_mode"] = it.get("mode", "default")
                if it.get("game_day"):
                    self.data["game_day"] = it["game_day"]
                self.data["days"] = {}                 # variant changed → drop deltas
                needs_replan = True
            elif action == "reset_week":
                self._reset_to_base(keep_persist=True)
            elif action == "persist_current_changes":
                for c in self.data["constraints"]:
                    c["persist"] = True
            # add_todo / complete_todo handled in inbox via TodoStore
        return needs_replan

    def set_days(self, days: dict, rationale: str) -> None:
        self.data["days"] = days
        self.data["replan_rationale"] = rationale
        self.data["replanned_at"] = datetime.now().isoformat(timespec="seconds")

    # ---- reset (called by reset.py and reset_week intent) -------------
    def _reset_to_base(self, keep_persist: bool) -> None:
        base = plan.load_base()
        kept = [c for c in self.data["constraints"] if c.get("persist")] \
            if keep_persist else []
        fresh = WeekState.fresh(base, self.data["week_of"], kept)
        self.data = fresh.data
        if kept:                                       # re-apply surviving constraints
            self.apply_intents([{"action": "add_constraint", **c} for c in kept])

    def weekly_reset(self) -> None:
        base = plan.load_base()
        kept = [c for c in self.data["constraints"] if c.get("persist")]
        self.data = WeekState.fresh(base, _monday_of(date.today()).isoformat(),
                                    kept).data