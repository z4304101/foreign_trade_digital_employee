from datetime import datetime, timedelta, timezone

import pytest

from history_learning.models import HistoricalEmail


def load_selection_functions():
    try:
        from history_learning.selection import (
            months_ago,
            select_recent_history,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"history_learning.selection is missing: {exc}"
        )

    return months_ago, select_recent_history


def make_record(
    message_id: str,
    sent_at: datetime,
) -> HistoricalEmail:
    return HistoricalEmail(
        message_id=message_id,
        mailbox="Sent",
        direction="outgoing",
        sender="sales@example.cn",
        recipients="customer@example.com",
        subject="Hello",
        sent_at=sent_at,
        body="Thanks",
        customer_email="customer@example.com",
        company_domain="example.com",
    )


def test_six_month_cutoff_is_calendar_based():
    months_ago, _ = load_selection_functions()

    now = datetime(
        2026,
        9,
        14,
        12,
        tzinfo=timezone.utc,
    )

    assert months_ago(
        now,
        6,
    ) == datetime(
        2026,
        3,
        14,
        12,
        tzinfo=timezone.utc,
    )


def test_month_end_is_clamped():
    months_ago, _ = load_selection_functions()

    now = datetime(
        2026,
        8,
        31,
        12,
        tzinfo=timezone.utc,
    )

    assert months_ago(
        now,
        6,
    ) == datetime(
        2026,
        2,
        28,
        12,
        tzinfo=timezone.utc,
    )


def test_message_before_six_month_cutoff_is_excluded():
    _, select_recent_history = (
        load_selection_functions()
    )

    now = datetime(
        2026,
        9,
        14,
        12,
        tzinfo=timezone.utc,
    )

    cutoff = datetime(
        2026,
        3,
        14,
        12,
        tzinfo=timezone.utc,
    )

    records = [
        make_record(
            "<before@example.com>",
            cutoff - timedelta(seconds=1),
        ),
        make_record(
            "<at-cutoff@example.com>",
            cutoff,
        ),
    ]

    selected = select_recent_history(
        records,
        now=now,
    )

    assert [
        item.message_id
        for item in selected
    ] == [
        "<at-cutoff@example.com>",
    ]


def test_history_keeps_latest_1000_inside_window():
    _, select_recent_history = (
        load_selection_functions()
    )

    now = datetime(
        2026,
        9,
        14,
        12,
        tzinfo=timezone.utc,
    )

    start = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    records = [
        make_record(
            f"<m{index}@example.com>",
            start + timedelta(minutes=index),
        )
        for index in range(1005)
    ]

    selected = select_recent_history(
        records,
        now=now,
    )

    assert len(selected) == 1000

    assert (
        selected[0].message_id
        == "<m5@example.com>"
    )

    assert (
        selected[-1].message_id
        == "<m1004@example.com>"
    )

    assert selected == sorted(
        selected,
        key=lambda item: item.sent_at,
    )
