from email.message import EmailMessage

from brief import inbox


def test_normalize_strips_dots_and_plus():
    assert inbox._normalize_gmail("e.lubbock+todo@gmail.com") == "elubbock@gmail.com"


def test_normalize_googlemail_alias():
    assert inbox._normalize_gmail("elubbock@googlemail.com") == "elubbock@gmail.com"


def test_normalize_case_insensitive():
    assert inbox._normalize_gmail("ELubbock@Gmail.com") == "elubbock@gmail.com"


def test_is_owner_with_display_name():
    assert inbox._is_owner("Ethan Lubbock <e.lubbock@gmail.com>") is True


def test_is_owner_rejects_stranger():
    assert inbox._is_owner("someone@evil.com") is False


def test_is_owner_rejects_spoof_suffix():
    # substring tricks shouldn't pass the normalized equality check
    assert inbox._is_owner("elubbock@gmail.com.evil.com") is False


def test_body_text_plain():
    msg = EmailMessage()
    msg.set_content("add: buy flowers")
    assert "buy flowers" in inbox._body_text(msg)


def test_body_text_multipart_prefers_plain():
    msg = EmailMessage()
    msg.set_content("plain version here")
    msg.add_alternative("<p>html version</p>", subtype="html")
    body = inbox._body_text(msg)
    assert "plain version" in body
    assert "<p>" not in body