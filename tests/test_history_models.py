from datetime import datetime, timezone

from history_learning.models import (
    HistoricalEmail,
    LearningSummary,
    StyleProfile,
)
from mail_reader.parser import parse_email


def test_parse_email_preserves_to_header():
    raw = (
        b"From: Pierre <pierre@example.com>\r\n"
        b"To: sales@example.cn\r\n"
        b"Subject: Hello\r\n"
        b"Message-ID: <m1@example.com>\r\n"
        b"\r\n"
        b"Body"
    )

    mail = parse_email(raw)

    assert mail.recipients == "sales@example.cn"


def test_historical_email_carries_direction_and_identity():
    record = HistoricalEmail(
        message_id="<m1@example.com>",
        mailbox="Sent",
        direction="outgoing",
        sender="sales@example.cn",
        recipients="pierre@example.com",
        subject="Re: Hello",
        sent_at=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
        body="Thanks",
        customer_email="pierre@example.com",
        company_domain="example.com",
    )

    assert record.direction == "outgoing"
    assert record.customer_email == "pierre@example.com"
    assert record.company_domain == "example.com"


def test_style_profile_defaults_are_empty_and_editable():
    profile = StyleProfile()

    assert profile.preferred_tone == ""
    assert profile.typical_length == ""
    assert profile.manual_overrides == {}

    profile.manual_overrides["preferred_tone"] = "professional"

    assert (
        profile.manual_overrides["preferred_tone"]
        == "professional"
    )


def test_learning_summary_preserves_learning_counts():
    summary = LearningSummary(
        scanned=100,
        learned=80,
        skipped=15,
        failed=5,
        sent_mailbox_found=True,
        style_profile_updated=True,
    )

    assert summary.scanned == 100
    assert summary.learned == 80
    assert summary.skipped == 15
    assert summary.failed == 5
    assert summary.sent_mailbox_found is True
    assert summary.style_profile_updated is True
    assert summary.warning == ""
