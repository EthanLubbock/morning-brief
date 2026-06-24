import imaplib
import email
from email.utils import parseaddr
from . import config, llm, plan
from .state import WeekState
from .todos import TodoStore
from .mailer import Mailer


def _normalize_gmail(addr: str) -> str:
    addr = addr.strip().lower()
    if "@" not in addr:
        return ""
    local, domain = addr.rsplit("@", 1)
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


_OWNER_N = _normalize_gmail(config.OWNER_EMAIL)


def _is_owner(from_header: str) -> bool:
    _, addr = parseaddr(from_header)
    return _normalize_gmail(addr) == _OWNER_N


def _body_text(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
        return ""
    return msg.get_payload(decode=True).decode(errors="ignore")


class InboxProcessor:
    def __init__(self):
        self.mailer = Mailer()

    def run(self) -> None:
        imap = imaplib.IMAP4_SSL(config.IMAP_HOST)
        imap.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
        imap.select("INBOX")
        # server-side pre-filter; _is_owner is the real gate
        _, ids = imap.search(None, "UNSEEN", "FROM", config.OWNER_EMAIL)
        for num in ids[0].split():
            _, data = imap.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            imap.store(num, "+FLAGS", "\\Seen")       # mark read regardless
            if not _is_owner(msg["From"]):            # spoof / stray → ignore silently
                continue
            self._handle(msg)
        imap.logout()

    def _handle(self, msg) -> None:
        body = _body_text(msg)
        intents = llm.parse_email(body)
        state = WeekState.load()
        todos = TodoStore()
        applied = []

        for it in intents:                            # todo intents act on TodoStore
            if it["action"] == "add_todo":
                todos.add(it["title"], it.get("priority", "medium"), it.get("due"))
                applied.append(f"Added todo: {it['title']}")
            elif it["action"] == "complete_todo":
                done = todos.complete(it.get("match", ""))
                applied.append(f"Completed: {done}" if done
                               else f"No open todo matching '{it.get('match')}'")
        todos.save()

        needs_replan = state.apply_intents(intents)   # schedule-affecting intents
        if needs_replan:
            base = plan.load_base()
            days, rationale = llm.replan_week(base, state.data)
            state.set_days(days, rationale)
            applied.append(f"Week adjusted: {rationale}")
        state.save()

        self._confirm(msg, intents, applied)

    def _confirm(self, msg, intents, applied) -> None:
        if not intents:
            body = ("I couldn't find anything actionable in that email.\n"
                    "Try: 'add: buy flowers (high)', 'can't do Thursday morning, "
                    "dentist', 'game Saturday', or 'done with ring chase'.")
        else:
            body = "Done:\n" + "\n".join(f"• {a}" for a in applied)
        self.mailer.send_to_owner(
            subject="Re: " + (msg["Subject"] or "your note"),
            body=body, in_reply_to=msg.get("Message-ID"))


if __name__ == "__main__":
    InboxProcessor().run()