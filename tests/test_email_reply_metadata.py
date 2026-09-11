from mail_reader.parser import parse_email


def test_parse_email_preserves_reply_metadata():
    raw_email = (
        b"From: Michael Brown <michael@customer.com>\r\n"
        b"To: sales@example.com\r\n"
        b"Reply-To: procurement@customer.com\r\n"
        b"Subject: Request for Quotation - Model R2\r\n"
        b"Date: Fri, 11 Sep 2026 18:30:00 +0800\r\n"
        b"Message-ID: <customer-message-001@example.com>\r\n"
        b"References: <previous-message-001@example.com>\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Dear Sales Team,\r\n"
        b"We would like to request a quotation for Model R2.\r\n"
    )

    mail = parse_email(raw_email)

    assert mail.sender == "Michael Brown <michael@customer.com>"
    assert mail.subject == "Request for Quotation - Model R2"

    assert mail.reply_to == "procurement@customer.com"
    assert mail.message_id == "<customer-message-001@example.com>"
    assert mail.references == "<previous-message-001@example.com>"