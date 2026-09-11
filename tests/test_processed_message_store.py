from pathlib import Path


def test_message_id_is_not_processed_initially(
    tmp_path,
):
    from mail_reader.processed_store import (
        is_message_processed,
    )

    store_path = tmp_path / "processed_message_ids.txt"

    result = is_message_processed(
        message_id="<message-001@example.com>",
        store_path=store_path,
    )

    assert result is False


def test_mark_message_processed_persists_message_id(
    tmp_path,
):
    from mail_reader.processed_store import (
        is_message_processed,
        mark_message_processed,
    )

    store_path = tmp_path / "processed_message_ids.txt"

    mark_message_processed(
        message_id="<message-001@example.com>",
        store_path=store_path,
    )

    assert is_message_processed(
        message_id="<message-001@example.com>",
        store_path=store_path,
    ) is True


def test_mark_message_processed_does_not_duplicate_id(
    tmp_path,
):
    from mail_reader.processed_store import (
        mark_message_processed,
    )

    store_path = tmp_path / "processed_message_ids.txt"

    message_id = "<message-001@example.com>"

    mark_message_processed(
        message_id=message_id,
        store_path=store_path,
    )

    mark_message_processed(
        message_id=message_id,
        store_path=store_path,
    )

    lines = store_path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert lines == [
        "<message-001@example.com>"
    ]


def test_empty_message_id_is_never_treated_as_processed(
    tmp_path,
):
    from mail_reader.processed_store import (
        is_message_processed,
    )

    store_path = tmp_path / "processed_message_ids.txt"

    assert is_message_processed(
        message_id="",
        store_path=store_path,
    ) is False

    assert is_message_processed(
        message_id=None,
        store_path=store_path,
    ) is False


def test_empty_message_id_is_not_saved(
    tmp_path,
):
    from mail_reader.processed_store import (
        mark_message_processed,
    )

    store_path = tmp_path / "processed_message_ids.txt"

    mark_message_processed(
        message_id="",
        store_path=store_path,
    )

    mark_message_processed(
        message_id=None,
        store_path=store_path,
    )

    assert not store_path.exists()