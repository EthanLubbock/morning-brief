import json
import logging
from openai import OpenAI
from . import config, plan, calendar_feed

log = logging.getLogger("brief.llm")
_client = OpenAI(api_key=config.OPENAI_API_KEY)

VALID_ACTIONS = {"add_constraint", "set_week_mode", "add_todo",
                 "complete_todo", "reset_week", "persist_current_changes"}

PARSE_SYSTEM = """You convert a personal email into scheduling intents.
Respond with ONLY a JSON object {"intents": [ ... ]} — no prose, no markdown.
Each intent has an "action" plus action-specific fields:

- add_constraint: applies_to (list of lowercase weekdays), constraint (short text),
  reason (optional text), persist (bool, default false)
- set_week_mode: mode ("default" or "game"), game_day (lowercase weekday, optional)
- add_todo: title (text), priority ("high"|"medium"|"low"), due ("YYYY-MM-DD" or null)
- complete_todo: match (text fragment identifying the task to mark done)
- reset_week: no fields
- persist_current_changes: no fields

A message may contain several intents. Examples:
"Can't get up early Thursday, dentist at 8" ->
 {"intents":[{"action":"add_constraint","applies_to":["thursday"],
   "constraint":"no early morning","reason":"dentist at 8","persist":false}]}
"I'll play hockey this Saturday" ->
 {"intents":[{"action":"set_week_mode","mode":"game","game_day":"saturday"}]}
"Add: buy wedding flowers, high priority" ->
 {"intents":[{"action":"add_todo","title":"buy wedding flowers","priority":"high","due":null}]}
"Done chasing the ring sizing" ->
 {"intents":[{"action":"complete_todo","match":"ring"}]}
If nothing is actionable, return {"intents": []}."""


def parse_email(body: str) -> list[dict]:
    try:
        resp = _client.chat.completions.create(
            model=config.OPENAI_MODEL, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": PARSE_SYSTEM},
                      {"role": "user", "content": body[:4000]}],
        )
        raw = resp.choices[0].message.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        intents = data.get("intents", []) if isinstance(data, dict) else []
        return [i for i in intents
                if isinstance(i, dict) and i.get("action") in VALID_ACTIONS]
    except Exception:
        log.exception("parse_email failed")          # visible in journalctl
        return []                                     # safe default: do nothing


def replan_week(base: dict, state_data: dict) -> tuple[dict, str]:
    """Return ({day: delta}, rationale). Falls back to plain notes on failure."""
    upcoming = [
        {"title": e.get("title"), "date": e.get("date"), "role": e.get("role")}
        for e in calendar_feed.upcoming_events(7)
        if e.get("role") in ("mine", "shared")
    ]
    payload = {
        "week_mode": state_data["week_mode"],
        "active_variant": base["variants"][state_data["week_mode"]],
        "constraints": state_data["constraints"],
        "calendar": upcoming,
        "rules": base["replan_rules"],
    }
    system = (
        "Adjust a weekly training plan around constraints and fixed calendar events. "
        "Return ONLY days that change, as deltas with keys: summary, moved_to, note. "
        "Obey the rules exactly. Calendar events are immovable. "
        "Output ONLY a JSON object: {\"days\": {day: {...}}, \"rationale\": \"one sentence\"}."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload)},
    ]
    last_exc = None
    for attempt in range(1, 3):  # max 2 attempts
        try:
            resp = _client.chat.completions.create(
                model=config.OPENAI_MODEL, temperature=0,
                response_format={"type": "json_object"},
                messages=messages,
            )
            raw = resp.choices[0].message.content.strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            out = json.loads(raw)
            return out.get("days", {}), out.get("rationale", "")
        except json.JSONDecodeError as exc:
            last_exc = exc
            log.warning("replan_week attempt %d returned invalid JSON: %s", attempt, exc)
            # Feed the bad response back so the model can self-correct
            messages.append({"role": "assistant", "content": resp.choices[0].message.content})
            messages.append({"role": "user", "content": "That was not valid JSON. Return ONLY the JSON object, no prose or markdown."})
        except Exception as exc:
            last_exc = exc
            log.exception("replan_week attempt %d failed", attempt)
            break  # non-JSON errors won't improve on retry

    log.error("replan_week giving up after retries: %s", last_exc)
    days = {}
    for c in state_data["constraints"]:
        for d in c.get("applies_to", []):
            days.setdefault(d, {}).setdefault("note", c.get("raw", ""))
    return days, "Applied constraints as notes (replan unavailable)."