def test_find_drafts_mailbox_from_special_use_flag():
    from mail_writer.draft_client import find_drafts_mailbox

    mailboxes = [
        b'() "/" "INBOX"',
        b'(\\Drafts) "/" "&g0l6P3ux-"',
        b'(\\Sent) "/" "&XfJT0ZAB-"',
        b'(\\Trash) "/" "&XfJSIJZk-"',
        b'(\\Junk) "/" "&V4NXPpCuTvY-"',
    ]

    result = find_drafts_mailbox(mailboxes)

    assert result == "&g0l6P3ux-"


def test_find_drafts_mailbox_uses_standard_name_as_fallback():
    from mail_writer.draft_client import find_drafts_mailbox

    mailboxes = [
        b'() "/" "INBOX"',
        b'() "/" "Drafts"',
        b'() "/" "Sent"',
    ]

    result = find_drafts_mailbox(mailboxes)

    assert result == "Drafts"


def test_find_drafts_mailbox_fails_when_not_found():
    import pytest

    from mail_writer.draft_client import find_drafts_mailbox

    mailboxes = [
        b'() "/" "INBOX"',
        b'(\\Sent) "/" "Sent"',
    ]

    with pytest.raises(
        ValueError,
        match="drafts mailbox",
    ):
        find_drafts_mailbox(mailboxes)
def test_save_draft_appends_message_to_drafts_mailbox():
    from email.message import EmailMessage

    from mail_reader.config import MailConfig
    from mail_writer.draft_client import save_draft

    calls = {}

    class FakeIMAP:
        def __init__(
            self,
            host,
            port,
        ):
            calls["host"] = host
            calls["port"] = port

        def login(
            self,
            user,
            password,
        ):
            calls["login"] = (
                user,
                password,
            )

            return "OK", [b"LOGIN completed"]

        def list(self):
            return (
                "OK",
                [
                    b'() "/" "INBOX"',
                    b'(\\Drafts) "/" "&g0l6P3ux-"',
                    b'(\\Sent) "/" "&XfJT0ZAB-"',
                ],
            )

        def append(
            self,
            mailbox,
            flags,
            date_time,
            message,
        ):
            calls["append"] = {
                "mailbox": mailbox,
                "flags": flags,
                "date_time": date_time,
                "message": message,
            }

            return "OK", [b"APPEND completed"]

        def logout(self):
            calls["logout"] = True

            return "BYE", [b"LOGOUT completed"]

    config = MailConfig(
        email_user="sales@example.com",
        auth_code="test-auth-code",
        imap_host="imap.example.com",
        imap_port=993,
    )

    message = EmailMessage()

    message["From"] = "sales@example.com"
    message["To"] = "customer@example.com"
    message["Subject"] = "Re: Model R2 Inquiry"

    message.set_content(
        "Dear Customer,\n\n"
        "Thank you for your inquiry.\n"
    )

    mailbox = save_draft(
        config=config,
        message=message,
        client_factory=FakeIMAP,
    )

    assert mailbox == "&g0l6P3ux-"

    assert calls["host"] == "imap.example.com"
    assert calls["port"] == 993

    assert calls["login"] == (
        "sales@example.com",
        "test-auth-code",
    )

    assert calls["append"]["mailbox"] == "&g0l6P3ux-"

    assert "\\Draft" in calls["append"]["flags"]

    raw_message = calls["append"]["message"]

    assert isinstance(raw_message, bytes)
    assert b"Re: Model R2 Inquiry" in raw_message
    assert b"customer@example.com" in raw_message
    assert b"Thank you for your inquiry." in raw_message

    assert calls["logout"] is True