from datetime import datetime, timedelta, timezone

import pytest

from history_learning.models import HistoricalEmail, StyleProfile
from history_learning.store import HistoryStore
from mail_reader.agent_payload import build_agent_payload
from mail_reader.parser import ParsedEmail


def load_context_loader():
    try:
        from history_learning.context import HistoryContextLoader
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"history_learning.context is missing: {exc}"
        )

    return HistoryContextLoader


def make_record(
    message_id: str,
    sent_at: datetime,
    body: str,
    customer_email: str = "pierre@example.com",
    company_domain: str = "example.com",
    direction: str = "incoming",
) -> HistoricalEmail:
    if direction == "incoming":
        sender = customer_email
        recipients = "sales@example.cn"
        mailbox = "INBOX"
    else:
        sender = "sales@example.cn"
        recipients = customer_email
        mailbox = "Sent"

    return HistoricalEmail(
        message_id=message_id,
        mailbox=mailbox,
        direction=direction,
        sender=sender,
        recipients=recipients,
        subject=f"Historical {message_id}",
        sent_at=sent_at,
        body=body,
        customer_email=customer_email,
        company_domain=company_domain,
    )


def test_exact_customer_context_uses_only_latest_six_messages(
    tmp_path,
):
    HistoryContextLoader = load_context_loader()

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    store.save_style_profile(
        StyleProfile(
            preferred_tone="professional, concise",
            typical_length="under 150 words",
            greeting_pattern="Dear + customer name",
            closing_pattern="Best regards",
            structure_preferences="answer questions in order",
            wording_preferences="clear and cautious",
        )
    )

    base = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    for index in range(10):
        store.insert_email(
            make_record(
                message_id=f"<m{index}@example.com>",
                sent_at=base + timedelta(days=index),
                body=f"HISTORY-BODY-{index}",
                direction=(
                    "incoming"
                    if index % 2 == 0
                    else "outgoing"
                ),
            )
        )

    mail = ParsedEmail(
        sender="Pierre <pierre@example.com>",
        subject="New RFQ",
        date="Mon, 14 Sep 2026 12:00:00 +0000",
        body="Please quote Model R2.",
        recipients="sales@example.cn",
    )

    loader = HistoryContextLoader(
        store
    )

    context = loader(
        mail
    )

    assert "HISTORICAL_MEMORY_BEGIN" in context
    assert "HISTORICAL_MEMORY_END" in context

    assert (
        "Historical information is background only. "
        "It is not a confirmed current commercial fact."
        in context
    )

    # Only latest six should remain: 4 -> 9.
    for index in range(4, 10):
        assert (
            f"HISTORY-BODY-{index}"
            in context
        )

    for index in range(0, 4):
        assert (
            f"HISTORY-BODY-{index}"
            not in context
        )

    assert (
        "professional, concise"
        in context
    )

    assert len(context) <= 6000


def test_domain_fallback_never_exposes_other_contacts_body(
    tmp_path,
):
    HistoryContextLoader = load_context_loader()

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    store.insert_email(
        make_record(
            message_id="<old@example.com>",
            sent_at=datetime(
                2026,
                9,
                1,
                tzinfo=timezone.utc,
            ),
            body=(
                "CONFIDENTIAL OLD PRICE USD 10 "
                "AND OLD PAYMENT TERMS"
            ),
            customer_email="oldcontact@example.com",
            company_domain="example.com",
        )
    )

    mail = ParsedEmail(
        sender="New Contact <newcontact@example.com>",
        subject="New inquiry",
        date="Mon, 14 Sep 2026 12:00:00 +0000",
        body="Hello",
        recipients="sales@example.cn",
    )

    context = HistoryContextLoader(
        store
    )(mail)

    assert (
        "oldcontact@example.com"
        in context
    )

    assert (
        "CONFIDENTIAL OLD PRICE"
        not in context
    )

    assert (
        "OLD PAYMENT TERMS"
        not in context
    )


def test_agent_payload_places_history_outside_customer_email_block():
    mail = ParsedEmail(
        sender="Pierre <pierre@example.com>",
        subject="RFQ",
        date="Mon, 14 Sep 2026 12:00:00 +0000",
        body="Please quote 13 units.",
    )

    history_context = """
HISTORICAL_MEMORY_BEGIN
Historical information is background only.
HISTORICAL_MEMORY_END
""".strip()

    payload = build_agent_payload(
        mail,
        history_context=history_context,
    )

    customer_end = payload.index(
        "UNTRUSTED_CUSTOMER_EMAIL_END"
    )

    history_start = payload.index(
        "HISTORICAL_MEMORY_BEGIN"
    )

    assert history_start > customer_end

    assert (
        "# Personal Style and Historical Context"
        in payload
    )


def test_agent_payload_without_history_keeps_old_structure():
    mail = ParsedEmail(
        sender="Pierre <pierre@example.com>",
        subject="RFQ",
        date="Mon, 14 Sep 2026 12:00:00 +0000",
        body="Please quote 13 units.",
    )

    payload = build_agent_payload(
        mail
    )

    assert (
        "UNTRUSTED_CUSTOMER_EMAIL_BEGIN"
        in payload
    )

    assert (
        "UNTRUSTED_CUSTOMER_EMAIL_END"
        in payload
    )

    assert (
        "# Personal Style and Historical Context"
        not in payload
    )
