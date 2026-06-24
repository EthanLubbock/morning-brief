import smtplib
from email.message import EmailMessage
from email.utils import parseaddr
from . import config


class Mailer:
    def send(self, to: str, subject: str, body: str,
             in_reply_to: str | None = None) -> None:
        msg = EmailMessage()
        msg["From"] = config.GMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        if in_reply_to:                       # threads the confirmation reply
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        msg.set_content(body)
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as s:
            s.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            s.send_message(msg)

    def send_to_owner(self, subject: str, body: str,
                      in_reply_to: str | None = None) -> None:
        self.send(config.OWNER_EMAIL, subject, body, in_reply_to)