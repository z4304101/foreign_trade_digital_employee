from datetime import datetime, timezone

import pytest

from mail_reader.parser import parse_email


def test_parse_email_preserves_to_header():
    raw = (
        b"From: Pierre <pierre@example.com>\r\n"
        b"To: sales@example.cn\r\n"
        b"Subject: Hello\r\n"
        b"Message-ID: <m1@example.com>\r\n"
        b"\r\nBody"
    )

    mail = parse_email(raw)

    assert getattr(mail, "recipients", None) == "sales@example.cn"


def test_historical_email_carries_direction_and_identity():
    try:
        from history_learning.models import HistoricalEmail
    except ModuleNotFoundError as exc:
        pytest.fail(f"history_learning.models is missing: {exc}")

    record = HistoricalEmail(
        message_id="<m1@example.com>",
        mailbox="Sent",
        direction="outgoing",
        sender="sales@example.cn",
        recipients="pierre@example.com",
        subject="Re: Hello",
        sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        body="Thanks",
        customer_email="pierre@example.com",
        company_domain="example.com",
    )

    assert record.direction == "outgoing"
    assert record.customer_email == "pierre@example.com"
