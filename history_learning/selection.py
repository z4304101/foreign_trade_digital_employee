import calendar
from datetime import datetime
from email.utils import parsedate_to_datetime

from history_learning.models import HistoricalEmail


def parse_mail_datetime(
    value: str,
) -> datetime | None:
    if not value or not value.strip():
        return None

    try:
        parsed = parsedate_to_datetime(
            value
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ):
        return None

    if parsed.tzinfo is None:
        local_timezone = (
            datetime.now()
            .astimezone()
            .tzinfo
        )

        parsed = parsed.replace(
            tzinfo=local_timezone
        )

    return parsed


def months_ago(
    now: datetime,
    months: int,
) -> datetime:
    if months < 0:
        raise ValueError(
            "months must be >= 0"
        )

    total_months = (
        now.year * 12
        + now.month
        - 1
        - months
    )

    year, month_index = divmod(
        total_months,
        12,
    )

    month = month_index + 1

    max_day = calendar.monthrange(
        year,
        month,
    )[1]

    day = min(
        now.day,
        max_day,
    )

    return now.replace(
        year=year,
        month=month,
        day=day,
    )


def select_recent_history(
    records: list[HistoricalEmail],
    now: datetime,
    months: int = 6,
    limit: int = 1000,
) -> list[HistoricalEmail]:
    if limit < 0:
        raise ValueError(
            "limit must be >= 0"
        )

    cutoff = months_ago(
        now,
        months,
    )

    eligible = [
        record
        for record in records
        if record.sent_at >= cutoff
        and record.sent_at <= now
    ]

    eligible.sort(
        key=lambda item: item.sent_at,
        reverse=True,
    )

    selected = eligible[:limit]

    selected.sort(
        key=lambda item: item.sent_at
    )

    return selected
