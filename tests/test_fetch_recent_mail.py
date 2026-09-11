def test_fetch_recent_raw_emails_returns_oldest_to_newest(
    monkeypatch,
):
    from mail_reader.imap_client import (
        fetch_recent_raw_emails,
    )
    from mail_reader.config import MailConfig

    class FakeIMAP:
        def __init__(
            self,
            host,
            port,
        ):
            self.host = host
            self.port = port

        def login(
            self,
            user,
            password,
        ):
            return "OK", [b"logged in"]

        def select(
            self,
            mailbox,
        ):
            assert mailbox == "INBOX"
            return "OK", [b"3"]

        def search(
            self,
            charset,
            criterion,
        ):
            assert charset is None
            assert criterion == "ALL"

            return (
                "OK",
                [b"101 102 103"],
            )

        def fetch(
            self,
            message_id,
            query,
        ):
            assert query == "(RFC822)"

            messages = {
                b"101": b"Subject: First\r\n\r\nFirst body",
                b"102": b"Subject: Second\r\n\r\nSecond body",
                b"103": b"Subject: Third\r\n\r\nThird body",
            }

            return (
                "OK",
                [
                    (
                        b"RFC822",
                        messages[message_id],
                    )
                ],
            )

        def logout(self):
            return "BYE", [b"logout"]

    monkeypatch.setattr(
        "mail_reader.imap_client.imaplib.IMAP4_SSL",
        FakeIMAP,
    )

    config = MailConfig(
        email_user="test@example.com",
        auth_code="test-auth-code",
        imap_host="imap.example.com",
        imap_port=993,
    )

    emails = fetch_recent_raw_emails(
        config=config,
        limit=2,
    )

    assert emails == [
        b"Subject: Second\r\n\r\nSecond body",
        b"Subject: Third\r\n\r\nThird body",
    ]


def test_fetch_recent_raw_emails_returns_empty_when_inbox_empty(
    monkeypatch,
):
    from mail_reader.imap_client import (
        fetch_recent_raw_emails,
    )
    from mail_reader.config import MailConfig

    class FakeIMAP:
        def __init__(
            self,
            host,
            port,
        ):
            pass

        def login(
            self,
            user,
            password,
        ):
            return "OK", [b"logged in"]

        def select(
            self,
            mailbox,
        ):
            return "OK", [b"0"]

        def search(
            self,
            charset,
            criterion,
        ):
            return "OK", [b""]

        def logout(self):
            return "BYE", [b"logout"]

    monkeypatch.setattr(
        "mail_reader.imap_client.imaplib.IMAP4_SSL",
        FakeIMAP,
    )

    config = MailConfig(
        email_user="test@example.com",
        auth_code="test-auth-code",
        imap_host="imap.example.com",
        imap_port=993,
    )

    emails = fetch_recent_raw_emails(
        config=config,
        limit=20,
    )

    assert emails == []