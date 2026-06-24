"""Live tests — real Gmail + iCloud. Run with: pytest -m live

Sending mail and connecting to IMAP need a real bot account in .env.
Calendar tests skip themselves if the ICS URLs aren't set.
"""
import imaplib
import os

import pytest

from brief import config
from brief.mailer import Mailer

pytestmark = pytest.mark.live

_NEEDS_MAIL = pytest.mark.skipif(
    os.environ.get("GMAIL_APP_PASSWORD", "placeholder") == "placeholder",
    reason="real Gmail credentials not set")


@_NEEDS_MAIL
def test_smtp_send_to_owner():
    # success == no exception; check your inbox for the message
    Mailer().send_to_owner("morning-brief test",
                           "If you can read this, SMTP works.")


@_NEEDS_MAIL
def test_imap_login_and_select():
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST)
    try:
        imap.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
        typ, _ = imap.select("INBOX")
        assert typ == "OK"
    finally:
        imap.logout()


def test_calendar_fetch_returns_list():
    if not any(c["url"] for c in config.CALENDARS):
        pytest.skip("no ICS URLs configured")
    from brief import calendar_feed
    events = calendar_feed.upcoming_events(7)
    assert isinstance(events, list)
    for e in events:
        assert {"date", "time", "title", "role"} <= set(e)