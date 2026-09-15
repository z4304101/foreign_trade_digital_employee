from pathlib import Path

from history_learning.store import HistoryStore
from mail_reader.processed_store import (
    is_message_processed,
    mark_message_processed,
)


def seed_processed_store_from_history(
    store: HistoryStore,
    processed_store_path: Path,
) -> int:
    """
    Mark historical incoming emails as already handled.

    Purpose:
    - historical INBOX mail remains available for learning
    - historical INBOX mail must never generate new drafts
    - Sent mail is NOT added to the reply baseline
    - future mail remains unprocessed

    Returns the number of newly added Message-IDs.
    """

    seeded = 0

    for message_id in (
        store.list_incoming_message_ids()
    ):
        if is_message_processed(
            message_id=message_id,
            store_path=processed_store_path,
        ):
            continue

        mark_message_processed(
            message_id=message_id,
            store_path=processed_store_path,
        )

        seeded += 1

    return seeded
