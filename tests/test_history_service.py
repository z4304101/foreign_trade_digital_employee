from datetime import datetime, timezone
from email.utils import format_datetime

import pytest

from history_learning.store import HistoryStore
from mail_reader.config import MailConfig
from mail_reader.parser import parse_email as real_parse_email


def load_service():
    try:
        import history_learning.service as service
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"history_learning.service is missing: {exc}"
        )

    return service


class FakeProvider:
    def __init__(self):
        self.calls = []

    def generate_reply(
        self,
        skill_text: str,
        customer_email: str,
    ) -> str:
        self.calls.append(
            {
                "skill_text": skill_text,
                "customer_email": customer_email,
            }
        )

        return """
        {
          "preferred_tone": "professional, concise",
          "typical_length": "under 150 words",
          "greeting_pattern": "Dear + customer name",
          "closing_pattern": "Best regards",
          "structure_preferences": "answer questions in order",
          "wording_preferences": "avoid unsupported commitments"
        }
        """


def make_config() -> MailConfig:
    return MailConfig(
        email_user="sales@example.cn",
        auth_code="fake-auth-code",
        imap_host="imap.example.com",
        imap_port=993,
    )


def make_raw_email(
    *,
    sender: str,
    recipients: str,
    subject: str,
    message_id: str,
    sent_at: datetime,
    body: str,
) -> bytes:
    text = (
        f"From: {sender}\r\n"
        f"To: {recipients}\r\n"
        f"Subject: {subject}\r\n"
        f"Message-ID: {message_id}\r\n"
        f"Date: {format_datetime(sent_at)}\r\n"
        "\r\n"
        f"{body}"
    )

    return text.encode(
        "utf-8"
    )


def test_initial_learning_indexes_valid_history_and_builds_style(
    tmp_path,
    monkeypatch,
):
    service = load_service()

    now = datetime(
        2026,
        9,
        14,
        12,
        tzinfo=timezone.utc,
    )

    valid_inbox = make_raw_email(
        sender="Pierre <pierre@example.com>",
        recipients="sales@example.cn",
        subject="RFQ for Model R2",
        message_id="<inbox-1@example.com>",
        sent_at=datetime(
            2026,
            9,
            1,
            10,
            tzinfo=timezone.utc,
        ),
        body=(
            "Hello, please quote 13 units "
            "and advise delivery terms."
        ),
    )

    system_inbox = make_raw_email(
        sender="noreply@example.com",
        recipients="sales@example.cn",
        subject="Verification Code",
        message_id="<system-1@example.com>",
        sent_at=datetime(
            2026,
            9,
            2,
            10,
            tzinfo=timezone.utc,
        ),
        body="Your code is 123456.",
    )

    valid_sent = make_raw_email(
        sender="sales@example.cn",
        recipients="Pierre <pierre@example.com>",
        subject="Re: RFQ for Model R2",
        message_id="<sent-1@example.com>",
        sent_at=datetime(
            2026,
            9,
            3,
            10,
            tzinfo=timezone.utc,
        ),
        body=(
            "Dear Pierre,\n\n"
            "Thank you for your inquiry. "
            "We will confirm the requested "
            "commercial details after review.\n\n"
            "Best regards"
        ),
    )

    old_sent = make_raw_email(
        sender="sales@example.cn",
        recipients="Old <old@example.com>",
        subject="Old message",
        message_id="<old-1@example.com>",
        sent_at=datetime(
            2026,
            3,
            1,
            10,
            tzinfo=timezone.utc,
        ),
        body="Dear Customer,\n\nOld email.\n\nBest regards",
    )

    def fake_fetch(
        config,
        mailbox,
        since,
        max_messages=1000,
    ):
        if mailbox == "INBOX":
            return [
                valid_inbox,
                system_inbox,
            ]

        if mailbox == "Sent":
            return [
                valid_sent,
                old_sent,
            ]

        raise AssertionError(
            f"Unexpected mailbox: {mailbox}"
        )

    monkeypatch.setattr(
        service,
        "fetch_folder_raw_emails",
        fake_fetch,
    )

    monkeypatch.setattr(
        service,
        "discover_sent_mailbox",
        lambda config: "Sent",
    )

    provider = FakeProvider()

    db_path = (
        tmp_path
        / "history.db"
    )

    summary = service.run_initial_learning(
        mail_config=make_config(),
        provider=provider,
        db_path=db_path,
        now=now,
    )

    assert summary.learned == 2
    assert summary.skipped == 2
    assert summary.failed == 0
    assert summary.sent_mailbox_found is True
    assert summary.style_profile_updated is True

    store = HistoryStore(
        db_path
    )

    assert store.email_exists(
        "<inbox-1@example.com>"
    )

    assert store.email_exists(
        "<sent-1@example.com>"
    )

    assert not store.email_exists(
        "<system-1@example.com>"
    )

    assert not store.email_exists(
        "<old-1@example.com>"
    )

    profile = store.get_style_profile()

    assert profile is not None
    assert (
        profile.preferred_tone
        == "professional, concise"
    )

    assert len(
        provider.calls
    ) == 1


def test_initial_learning_continues_when_sent_folder_missing(
    tmp_path,
    monkeypatch,
):
    service = load_service()

    now = datetime(
        2026,
        9,
        14,
        12,
        tzinfo=timezone.utc,
    )

    valid_inbox = make_raw_email(
        sender="Alice <alice@example.com>",
        recipients="sales@example.cn",
        subject="Product inquiry",
        message_id="<inbox-2@example.com>",
        sent_at=datetime(
            2026,
            9,
            5,
            10,
            tzinfo=timezone.utc,
        ),
        body="Hello, please send product information.",
    )

    def fake_fetch(
        config,
        mailbox,
        since,
        max_messages=1000,
    ):
        assert mailbox == "INBOX"

        return [
            valid_inbox
        ]

    monkeypatch.setattr(
        service,
        "fetch_folder_raw_emails",
        fake_fetch,
    )

    monkeypatch.setattr(
        service,
        "discover_sent_mailbox",
        lambda config: None,
    )

    db_path = (
        tmp_path
        / "history.db"
    )

    summary = service.run_initial_learning(
        mail_config=make_config(),
        provider=FakeProvider(),
        db_path=db_path,
        now=now,
    )

    assert summary.learned == 1
    assert summary.failed == 0
    assert summary.sent_mailbox_found is False
    assert summary.style_profile_updated is False
    assert "已发送" in summary.warning

    store = HistoryStore(
        db_path
    )

    assert store.email_exists(
        "<inbox-2@example.com>"
    )

    state = (
        store.get_learning_state()
    )

    assert (
        state[
            "initial_learning_completed"
        ]
        == "true"
    )


def test_one_broken_message_does_not_stop_later_messages(
    tmp_path,
    monkeypatch,
):
    service = load_service()

    now = datetime(
        2026,
        9,
        14,
        12,
        tzinfo=timezone.utc,
    )

    valid_inbox = make_raw_email(
        sender="David <david@example.com>",
        recipients="sales@example.cn",
        subject="Inquiry",
        message_id="<inbox-3@example.com>",
        sent_at=datetime(
            2026,
            9,
            6,
            10,
            tzinfo=timezone.utc,
        ),
        body="Please send more information.",
    )

    broken = b"BROKEN-HISTORICAL-MESSAGE"

    monkeypatch.setattr(
        service,
        "fetch_folder_raw_emails",
        lambda config, mailbox, since, max_messages=1000: (
            [
                broken,
                valid_inbox,
            ]
            if mailbox == "INBOX"
            else []
        ),
    )

    monkeypatch.setattr(
        service,
        "discover_sent_mailbox",
        lambda config: "Sent",
    )

    def fake_parse_email(
        raw_email,
    ):
        if raw_email == broken:
            raise ValueError(
                "broken historical email"
            )

        return real_parse_email(
            raw_email
        )

    monkeypatch.setattr(
        service,
        "parse_email",
        fake_parse_email,
    )

    db_path = (
        tmp_path
        / "history.db"
    )

    summary = service.run_initial_learning(
        mail_config=make_config(),
        provider=FakeProvider(),
        db_path=db_path,
        now=now,
    )

    assert summary.failed == 1
    assert summary.learned == 1

    store = HistoryStore(
        db_path
    )

    assert store.email_exists(
        "<inbox-3@example.com>"
    )
