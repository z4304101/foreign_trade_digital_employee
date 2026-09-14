from datetime import date

import pytest

from mail_reader.config import MailConfig


def load_source_functions():
    try:
        from history_learning.imap_source import (
            discover_sent_mailbox,
            fetch_folder_raw_emails,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"history_learning.imap_source is missing: {exc}"
        )

    return (
        discover_sent_mailbox,
        fetch_folder_raw_emails,
    )


class FakeIMAPClient:
    def __init__(
        self,
        list_rows=None,
        message_ids=b"",
        message_bodies=None,
    ):
        self.list_rows = list_rows or []
        self.message_ids = message_ids
        self.message_bodies = (
            message_bodies or {}
        )

        self.login_calls = []
        self.select_calls = []
        self.search_calls = []
        self.fetch_calls = []
        self.logout_called = False

    def login(
        self,
        username,
        password,
    ):
        self.login_calls.append(
            (username, password)
        )

        return (
            "OK",
            [b"logged in"],
        )

    def _simple_command(
        self,
        command,
        payload,
    ):
        return (
            "OK",
            [b"ID accepted"],
        )

    def list(self):
        return (
            "OK",
            self.list_rows,
        )

    def select(
        self,
        mailbox,
        readonly=False,
    ):
        self.select_calls.append(
            (mailbox, readonly)
        )

        return (
            "OK",
            [b"0"],
        )

    def search(
        self,
        charset,
        *criteria,
    ):
        self.search_calls.append(
            (charset, criteria)
        )

        return (
            "OK",
            [self.message_ids],
        )

    def fetch(
        self,
        message_id,
        query,
    ):
        self.fetch_calls.append(
            (message_id, query)
        )

        body = self.message_bodies[
            message_id
        ]

        return (
            "OK",
            [
                (
                    b"metadata",
                    body,
                )
            ],
        )

    def logout(self):
        self.logout_called = True

        return (
            "BYE",
            [b"logout"],
        )


def make_config():
    return MailConfig(
        email_user="sales@example.com",
        auth_code="fake-auth-code",
        imap_host="imap.example.com",
        imap_port=993,
    )


def test_discovers_sent_mailbox_from_special_use_flag(
    monkeypatch,
):
    discover_sent_mailbox, _ = (
        load_source_functions()
    )

    fake_client = FakeIMAPClient(
        list_rows=[
            (
                b'(\\HasNoChildren) "/" '
                b'"INBOX"'
            ),
            (
                b'(\\HasNoChildren \\Sent) '
                b'"/" "Sent"'
            ),
        ]
    )

    monkeypatch.setattr(
        "history_learning.imap_source."
        "imaplib.IMAP4_SSL",
        lambda **kwargs: fake_client,
    )

    result = discover_sent_mailbox(
        make_config()
    )

    assert result == "Sent"
    assert fake_client.logout_called is True


def test_discovers_sent_mailbox_by_common_name_fallback(
    monkeypatch,
):
    discover_sent_mailbox, _ = (
        load_source_functions()
    )

    fake_client = FakeIMAPClient(
        list_rows=[
            (
                b'(\\HasNoChildren) "/" '
                b'"INBOX"'
            ),
            (
                b'(\\HasNoChildren) "/" '
                b'"Sent Messages"'
            ),
        ]
    )

    monkeypatch.setattr(
        "history_learning.imap_source."
        "imaplib.IMAP4_SSL",
        lambda **kwargs: fake_client,
    )

    result = discover_sent_mailbox(
        make_config()
    )

    assert result == "Sent Messages"


def test_returns_none_when_sent_mailbox_is_not_found(
    monkeypatch,
):
    discover_sent_mailbox, _ = (
        load_source_functions()
    )

    fake_client = FakeIMAPClient(
        list_rows=[
            (
                b'(\\HasNoChildren) "/" '
                b'"INBOX"'
            ),
            (
                b'(\\HasNoChildren) "/" '
                b'"Archive"'
            ),
        ]
    )

    monkeypatch.setattr(
        "history_learning.imap_source."
        "imaplib.IMAP4_SSL",
        lambda **kwargs: fake_client,
    )

    result = discover_sent_mailbox(
        make_config()
    )

    assert result is None


def test_historical_folder_fetch_is_read_only_and_uses_peek(
    monkeypatch,
):
    _, fetch_folder_raw_emails = (
        load_source_functions()
    )

    fake_client = FakeIMAPClient(
        message_ids=b"1 2 3",
        message_bodies={
            b"1": b"mail-one",
            b"2": b"mail-two",
            b"3": b"mail-three",
        },
    )

    monkeypatch.setattr(
        "history_learning.imap_source."
        "imaplib.IMAP4_SSL",
        lambda **kwargs: fake_client,
    )

    result = fetch_folder_raw_emails(
        config=make_config(),
        mailbox="Sent",
        since=date(
            2026,
            3,
            14,
        ),
        max_messages=2,
    )

    assert result == [
        b"mail-two",
        b"mail-three",
    ]

    assert fake_client.select_calls == [
        (
            "Sent",
            True,
        )
    ]

    assert fake_client.search_calls == [
        (
            None,
            (
                "SINCE",
                "14-Mar-2026",
            ),
        )
    ]

    assert fake_client.fetch_calls == [
        (
            b"2",
            "(BODY.PEEK[])",
        ),
        (
            b"3",
            "(BODY.PEEK[])",
        ),
    ]

    assert fake_client.logout_called is True
