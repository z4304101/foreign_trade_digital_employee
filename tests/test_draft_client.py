def test_find_drafts_mailbox_from_special_use_flag():
    from mail_writer.draft_client import find_drafts_mailbox

    mailboxes = [
        b'() "/" "INBOX"',
        b'(\\Drafts) "/" "&g0l6P3ux-"',
        b'(\\Sent) "/" "&XfJT0ZAB-"',
        b'(\\Trash) "/" "&XfJSIJZk-"',
        b'(\\Junk) "/" "&V4NXPpCuTvY-"',
    ]

    result = find_drafts_mailbox(mailboxes)

    assert result == "&g0l6P3ux-"


def test_find_drafts_mailbox_uses_standard_name_as_fallback():
    from mail_writer.draft_client import find_drafts_mailbox

    mailboxes = [
        b'() "/" "INBOX"',
        b'() "/" "Drafts"',
        b'() "/" "Sent"',
    ]

    result = find_drafts_mailbox(mailboxes)

    assert result == "Drafts"


def test_find_drafts_mailbox_fails_when_not_found():
    import pytest

    from mail_writer.draft_client import find_drafts_mailbox

    mailboxes = [
        b'() "/" "INBOX"',
        b'(\\Sent) "/" "Sent"',
    ]

    with pytest.raises(
        ValueError,
        match="drafts mailbox",
    ):
        find_drafts_mailbox(mailboxes)