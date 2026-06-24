from datetime import date
from . import config, plan, bins, calendar_feed
from .state import WeekState
from .todos import TodoStore
from .mailer import Mailer

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday",
             "friday", "saturday", "sunday"]


def build_brief() -> tuple[str, str]:
    today = date.today()
    day = DAY_NAMES[today.weekday()]
    base = plan.load_base()
    state = WeekState.load()
    todos = TodoStore()

    session = plan.resolve_day(base, state.data["week_mode"], day,
                               state.data["days"].get(day))

    lines = [f"Morning Ethan,\n", "WORKOUT" +
             (f" — {session['note']}" if session.get("note") else "")]
    lines.append(session["summary"].rstrip())
    lines.append(f"\nDAILY\n{base['daily']}")

    events = calendar_feed.todays_events()
    if events:
        lines.append("\nTODAY")
        for e in events:
            tag = "  [shared]" if e["role"] == "shared" else ""
            lines.append(f"• {e['time']}  {e['title']}{tag}")

    b = bins.bin_line()
    if b:
        lines.append(f"\n{b}")
    warn = bins.expiry_warning()
    if warn:
        lines.append(warn)

    picked = todos.select(config.TODOS_IN_BRIEF)
    if picked:
        lines.append("\nTASKS")
        for i, t in enumerate(picked, 1):
            due = f" (due {t['due']})" if t["due"] else ""
            lines.append(f"{i}. {t['title']} ({t['priority']}){due}")

    mode_note = "default mode" if state.data["week_mode"] == "default" else "GAME week"
    rationale = state.data.get("replan_rationale", "")
    lines.append(f"\nThis week: {mode_note}." +
                 (f" {rationale}" if rationale else "") +
                 " Resets Sunday night.")
    lines.append("Reply to add tasks, log a game, or change the week.")

    subject = f"☀️ {today.strftime('%a %d %b')} — {session['type']}, {len(picked)} tasks"
    return subject, "\n".join(lines)


if __name__ == "__main__":
    subject, body = build_brief()
    Mailer().send_to_owner(subject, body)