from pathlib import Path
from typing import Optional


def _normalize_message_id(
    message_id: Optional[str],
) -> str:
    """
    Normalize a Message-ID before reading or writing it.

    Empty or None values are normalized to an empty string.
    """

    if not message_id:
        return ""

    return message_id.strip()


def _load_processed_message_ids(
    store_path: Path,
) -> set[str]:
    """
    Load processed Message-IDs from disk.

    If the store file does not exist yet,
    return an empty set.
    """

    if not store_path.exists():
        return set()

    content = store_path.read_text(
        encoding="utf-8",
    )

    return {
        line.strip()
        for line in content.splitlines()
        if line.strip()
    }


def is_message_processed(
    message_id: Optional[str],
    store_path: Path,
) -> bool:
    """
    Return True if the Message-ID has already
    been recorded as successfully processed.

    Empty Message-IDs are never considered processed.
    """

    normalized_id = _normalize_message_id(
        message_id
    )

    if not normalized_id:
        return False

    processed_ids = _load_processed_message_ids(
        store_path
    )

    return normalized_id in processed_ids


def mark_message_processed(
    message_id: Optional[str],
    store_path: Path,
) -> None:
    """
    Persist a successfully processed Message-ID.

    Rules:
    - Empty Message-IDs are ignored.
    - Duplicate Message-IDs are not written twice.
    - Parent directory is created when needed.
    """

    normalized_id = _normalize_message_id(
        message_id
    )

    if not normalized_id:
        return

    processed_ids = _load_processed_message_ids(
        store_path
    )

    if normalized_id in processed_ids:
        return

    store_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with store_path.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            normalized_id + "\n"
        )