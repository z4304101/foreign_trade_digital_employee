from datetime import datetime, timedelta, timezone

import pytest

from history_learning.models import (
    HistoricalEmail,
    StyleProfile,
)
from mail_reader.parser import ParsedEmail


def load_identity_functions():
    try:
        from history_learning.identity import (
            customer_identity,
            extract_domain,
            extract_email_address,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"history_learning.identity is missing: {exc}"
        )

    return (
        extract_email_address,
        extract_domain,
        customer_identity,
    )


def load_history_store():
    try:
        from history_learning.store import HistoryStore
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"history_learning.store is missing: {exc}"
        )

    return HistoryStore


def make_record(
    message_id: str,
    sent_at: datetime,
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
        subject="Hello",
        sent_at=sent_at,
        body="Thanks for your inquiry.",
        customer_email=customer_email,
        company_domain=company_domain,
    )


def test_extract_email_address_normalizes_case():
    (
        extract_email_address,
        _,
        _,
    ) = load_identity_functions()

    assert (
        extract_email_address(
            "Pierre <PIERRE@Example.com>"
        )
        == "pierre@example.com"
    )


def test_extract_domain_returns_lowercase_domain():
    (
        _,
        extract_domain,
        _,
    ) = load_identity_functions()

    assert (
        extract_domain(
            "pierre@Example.COM"
        )
        == "example.com"
    )


def test_incoming_customer_identity_uses_sender():
    (
        _,
        _,
        customer_identity,
    ) = load_identity_functions()

    mail = ParsedEmail(
        sender="Pierre <PIERRE@Example.com>",
        subject="RFQ",
        date="",
        body="Hello",
        recipients="sales@example.cn",
    )

    customer_email, domain = customer_identity(
        mail=mail,
        direction="incoming",
        own_email="sales@example.cn",
    )

    assert customer_email == "pierre@example.com"
    assert domain == "example.com"


def test_outgoing_customer_identity_excludes_own_address():
    (
        _,
        _,
        customer_identity,
    ) = load_identity_functions()

    mail = ParsedEmail(
        sender="sales@example.cn",
        subject="Re: RFQ",
        date="",
        body="Thanks",
        recipients=(
            "sales@example.cn, "
            "Pierre <PIERRE@Example.com>"
        ),
    )

    customer_email, domain = customer_identity(
        mail=mail,
        direction="outgoing",
        own_email="sales@example.cn",
    )

    assert customer_email == "pierre@example.com"
    assert domain == "example.com"


def test_store_inserts_email_once_by_message_id(
    tmp_path,
):
    HistoryStore = load_history_store()

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    record = make_record(
        "<m1@example.com>",
        datetime(
            2026,
            9,
            1,
            12,
            tzinfo=timezone.utc,
        ),
    )

    assert store.insert_email(record) is True
    assert store.insert_email(record) is False

    assert (
        store.email_exists(
            "<m1@example.com>"
        )
        is True
    )


def test_recent_for_customer_returns_newest_first(
    tmp_path,
):
    HistoryStore = load_history_store()

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    base = datetime(
        2026,
        9,
        1,
        12,
        tzinfo=timezone.utc,
    )

    store.insert_email(
        make_record(
            "<old@example.com>",
            base,
        )
    )

    store.insert_email(
        make_record(
            "<new@example.com>",
            base + timedelta(days=1),
        )
    )

    records = store.recent_for_customer(
        "pierre@example.com",
        limit=6,
    )

    assert [
        item.message_id
        for item in records
    ] == [
        "<new@example.com>",
        "<old@example.com>",
    ]


def test_recent_for_domain_never_returns_other_domain(
    tmp_path,
):
    HistoryStore = load_history_store()

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    now = datetime(
        2026,
        9,
        1,
        12,
        tzinfo=timezone.utc,
    )

    store.insert_email(
        make_record(
            "<example@example.com>",
            now,
            customer_email="pierre@example.com",
            company_domain="example.com",
        )
    )

    store.insert_email(
        make_record(
            "<other@other.com>",
            now + timedelta(hours=1),
            customer_email="alice@other.com",
            company_domain="other.com",
        )
    )

    records = store.recent_for_domain(
        "example.com",
        limit=3,
    )

    assert len(records) == 1

    assert (
        records[0].message_id
        == "<example@example.com>"
    )


def test_style_profile_and_manual_overrides_persist(
    tmp_path,
):
    HistoryStore = load_history_store()

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    profile = StyleProfile(
        preferred_tone="professional",
        typical_length="100-150 words",
        greeting_pattern="Dear + name",
        closing_pattern="Best regards",
        manual_overrides={
            "typical_length": "under 100 words",
        },
        updated_at="2026-09-14T12:00:00+00:00",
    )

    store.save_style_profile(
        profile
    )

    loaded = store.get_style_profile()

    assert loaded is not None
    assert (
        loaded.preferred_tone
        == "professional"
    )

    assert loaded.manual_overrides == {
        "typical_length": "under 100 words"
    }

    store.save_manual_style_overrides(
        {
            "preferred_tone": "friendly",
        }
    )

    loaded = store.get_style_profile()

    assert loaded is not None
    assert loaded.manual_overrides == {
        "preferred_tone": "friendly"
    }


def test_learning_state_round_trips(
    tmp_path,
):
    HistoryStore = load_history_store()

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    store.set_learning_state(
        {
            "initial_learning_completed": "true",
            "last_sent_message_id": "<m9@example.com>",
        }
    )

    state = store.get_learning_state()

    assert state[
        "initial_learning_completed"
    ] == "true"

    assert state[
        "last_sent_message_id"
    ] == "<m9@example.com>"
