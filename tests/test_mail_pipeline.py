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