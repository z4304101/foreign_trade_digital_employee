import re
from typing import Iterable


def _parse_mailbox_line(
    mailbox_line: bytes | str,
) -> tuple[list[str], str]:
    """
    Parse one IMAP LIST response line.

    Example:
        (\\Drafts) "/" "&g0l6P3ux-"

    Returns:
        (
            ["\\Drafts"],
            "&g0l6P3ux-",
        )
    """

    if isinstance(mailbox_line, bytes):
        text = mailbox_line.decode(
            "utf-8",
            errors="replace",
        )
    else:
        text = str(mailbox_line)

    text = text.strip()

    match = re.match(
        r'^\((?P<flags>[^)]*)\)\s+'
        r'(?P<delimiter>"[^"]*"|NIL)\s+'
        r'(?P<mailbox>".*"|[^\s]+)$',
        text,
    )

    if not match:
        return [], ""

    flags_text = match.group("flags").strip()

    flags = (
        flags_text.split()
        if flags_text
        else []
    )

    mailbox = match.group("mailbox").strip()

    if (
        len(mailbox) >= 2
        and mailbox.startswith('"')
        and mailbox.endswith('"')
    ):
        mailbox = mailbox[1:-1]

    return flags, mailbox


def find_drafts_mailbox(
    mailboxes: Iterable[bytes | str],
) -> str:
    """
    Find the Drafts mailbox from an IMAP LIST result.

    Priority:

    1. Mailbox explicitly marked with \\Drafts
    2. Standard mailbox names such as Drafts
    3. Raise ValueError if no drafts mailbox can be found

    Important:
    The actual mailbox name is returned unchanged.

    For example, NetEase 163 may return:

        (\\Drafts) "/" "&g0l6P3ux-"

    In that case this function returns:

        &g0l6P3ux-
    """

    parsed_mailboxes: list[
        tuple[list[str], str]
    ] = []

    for mailbox_line in mailboxes:
        flags, mailbox = _parse_mailbox_line(
            mailbox_line
        )

        if not mailbox:
            continue

        parsed_mailboxes.append(
            (flags, mailbox)
        )

        normalized_flags = {
            flag.lower()
            for flag in flags
        }

        if "\\drafts" in normalized_flags:
            return mailbox

    fallback_names = {
        "drafts",
        "draft",
        "草稿箱",
        "草稿",
    }

    for _, mailbox in parsed_mailboxes:
        if mailbox.strip().lower() in fallback_names:
            return mailbox

    raise ValueError(
        "drafts mailbox not found"
    )