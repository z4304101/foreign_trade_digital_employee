from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from history_learning.models import HistoricalEmail
from history_learning.store import HistoryStore
from mail_reader.processed_store import (
    is_message_processed,
)


def make_record(
    *,
    message_id,
    direction,
):
    if direction == "incoming":
        mailbox = "INBOX"
        sender = "Customer <customer@example.com>"
        recipients = "sales@example.cn"
    else:
        mailbox = "Sent"
        sender = "sales@example.cn"
        recipients = "Customer <customer@example.com>"

    return HistoricalEmail(
        message_id=message_id,
        mailbox=mailbox,
        direction=direction,
        sender=sender,
        recipients=recipients,
        subject="RFQ",
        sent_at=datetime(
            2026,
            9,
            10,
            10,
            tzinfo=timezone.utc,
        ),
        body="Historical email body",
        customer_email="customer@example.com",
        company_domain="example.com",
    )


def test_store_lists_only_historical_incoming_message_ids(
    tmp_path,
):
    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    store.insert_email(
        make_record(
            message_id="<old-inbox@example.com>",
            direction="incoming",
        )
    )

    store.insert_email(
        make_record(
            message_id="<old-sent@example.com>",
            direction="outgoing",
        )
    )

    assert (
        store.list_incoming_message_ids()
        == [
            "<old-inbox@example.com>"
        ]
    )


def test_seed_processed_store_marks_history_but_not_future_mail(
    tmp_path,
):
    try:
        from history_learning.reply_baseline import (
            seed_processed_store_from_history,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            "history_learning.reply_baseline "
            f"is missing: {exc}"
        )

    store = HistoryStore(
        tmp_path / "history.db"
    )
    store.initialize()

    old_inbox_id = (
        "<old-customer@example.com>"
    )
    old_sent_id = (
        "<old-sent@example.com>"
    )
    future_mail_id = (
        "<future-new@example.com>"
    )

    store.insert_email(
        make_record(
            message_id=old_inbox_id,
            direction="incoming",
        )
    )

    store.insert_email(
        make_record(
            message_id=old_sent_id,
            direction="outgoing",
        )
    )

    processed_path = (
        tmp_path
        / "processed_message_ids.txt"
    )

    seeded = (
        seed_processed_store_from_history(
            store=store,
            processed_store_path=processed_path,
        )
    )

    assert seeded == 1

    # Historical INBOX is now a reply baseline.
    assert is_message_processed(
        old_inbox_id,
        processed_path,
    )

    # Sent history is learning material only.
    assert not is_message_processed(
        old_sent_id,
        processed_path,
    )

    # A genuinely new email arriving later
    # must remain eligible for processing.
    assert not is_message_processed(
        future_mail_id,
        processed_path,
    )


def test_manual_initial_learning_builds_reply_baseline(
    tmp_path,
    monkeypatch,
):
    import learn_history

    db_path = (
        tmp_path
        / "history_learning.db"
    )

    processed_path = (
        tmp_path
        / "processed_message_ids.txt"
    )

    monkeypatch.setattr(
        learn_history,
        "HISTORY_DB_PATH",
        db_path,
    )

    monkeypatch.setattr(
        learn_history,
        "PROCESSED_STORE_PATH",
        processed_path,
        raising=False,
    )

    monkeypatch.setattr(
        learn_history,
        "load_mail_config",
        lambda: object(),
    )

    monkeypatch.setattr(
        learn_history,
        "load_llm_config",
        lambda: object(),
    )

    monkeypatch.setattr(
        learn_history,
        "create_llm_provider",
        lambda config: object(),
    )

    summary = SimpleNamespace(
        scanned=20,
        learned=13,
        skipped=7,
        failed=0,
        sent_mailbox_found=True,
        style_profile_updated=True,
        warning="",
    )

    monkeypatch.setattr(
        learn_history,
        "run_initial_learning",
        lambda **kwargs: summary,
    )

    calls = []

    def fake_seed(
        store,
        processed_store_path,
    ):
        calls.append(
            processed_store_path
        )
        return 12

    monkeypatch.setattr(
        learn_history,
        "seed_processed_store_from_history",
        fake_seed,
        raising=False,
    )

    result = learn_history.main()

    assert result is summary

    assert calls == [
        processed_path
    ]
