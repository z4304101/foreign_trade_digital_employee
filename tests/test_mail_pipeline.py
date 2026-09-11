from mail_reader.config import MailConfig


def test_mail_pipeline_fetches_and_parses_email(monkeypatch):
    raw_email = (
        b"From: Alex <alex@example.com>\r\n"
        b"To: sales@example.com\r\n"
        b"Subject: Inquiry for Model R2\r\n"
        b"Date: Fri, 11 Sep 2026 15:40:28 +0800\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Hello,\r\n"
        b"We are interested in Model R2 and would like to purchase 20 units.\r\n"
    )

    from mail_reader import pipeline

    monkeypatch.setattr(
        pipeline,
        "fetch_latest_raw_email",
        lambda config: raw_email,
    )

    config = MailConfig(
        email_user="test@example.com",
        auth_code="test-code",
        imap_host="imap.example.com",
        imap_port=993,
    )

    mail = pipeline.read_latest_email(config)

    assert mail.sender == "Alex <alex@example.com>"
    assert mail.subject == "Inquiry for Model R2"
    assert "Model R2" in mail.body
    assert "20 units" in mail.body
def test_read_recent_emails_fetches_and_parses_multiple_messages(
    monkeypatch,
):
    import mail_reader.pipeline as pipeline

    raw_email_1 = (
        b"From: Alice <alice@example.com>\r\n"
        b"To: sales@example.com\r\n"
        b"Subject: Inquiry A\r\n"
        b"Message-ID: <message-a@example.com>\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"First inquiry"
    )

    raw_email_2 = (
        b"From: Bob <bob@example.com>\r\n"
        b"To: sales@example.com\r\n"
        b"Subject: Inquiry B\r\n"
        b"Message-ID: <message-b@example.com>\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Second inquiry"
    )

    monkeypatch.setattr(
        pipeline,
        "fetch_recent_raw_emails",
        lambda config, limit=20: [
            raw_email_1,
            raw_email_2,
        ],
        raising=False,
    )

    emails = pipeline.read_recent_emails(
        config=object(),
        limit=20,
    )

    assert len(emails) == 2

    assert emails[0].sender == (
        "Alice <alice@example.com>"
    )
    assert emails[0].subject == "Inquiry A"
    assert emails[0].message_id == (
        "<message-a@example.com>"
    )

    assert emails[1].sender == (
        "Bob <bob@example.com>"
    )
    assert emails[1].subject == "Inquiry B"
    assert emails[1].message_id == (
        "<message-b@example.com>"
    )


def test_read_recent_emails_returns_empty_list(
    monkeypatch,
):
    import mail_reader.pipeline as pipeline

    monkeypatch.setattr(
        pipeline,
        "fetch_recent_raw_emails",
        lambda config, limit=20: [],
        raising=False,
    )

    emails = pipeline.read_recent_emails(
        config=object(),
        limit=20,
    )

    assert emails == []