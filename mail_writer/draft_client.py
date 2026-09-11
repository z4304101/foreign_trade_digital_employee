import imaplib
import re
from email import policy
from email.message import EmailMessage
from typing import Iterable

from mail_reader.config import MailConfig


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


def _status_is_ok(
    status: str | bytes,
) -> bool:
    """
    Normalize an IMAP status value.
    """

    if isinstance(status, bytes):
        status = status.decode(
            "ascii",
            errors="ignore",
        )

    return str(status).upper() == "OK"


def save_draft(
    config: MailConfig,
    message: EmailMessage,
    client_factory=imaplib.IMAP4_SSL,
) -> str:
    """
    Save an EmailMessage into the account's Drafts mailbox.

    This function DOES NOT send email.

    Workflow:
        LOGIN
        LIST
        locate \\Drafts
        APPEND with \\Draft flag
        LOGOUT

    Returns:
        The actual IMAP drafts mailbox name.
    """

    if not isinstance(message, EmailMessage):
        raise TypeError(
            "message must be an EmailMessage"
        )

    client = client_factory(
        config.imap_host,
        config.imap_port,
    )

    try:
        login_status, _ = client.login(
            config.email_user,
            config.auth_code,
        )

        if not _status_is_ok(login_status):
            raise RuntimeError(
                "IMAP login failed"
            )

        list_status, mailboxes = client.list()

        if not _status_is_ok(list_status):
            raise RuntimeError(
                "failed to list IMAP mailboxes"
            )

        if not mailboxes:
            raise ValueError(
                "drafts mailbox not found"
            )

        drafts_mailbox = find_drafts_mailbox(
            mailboxes
        )

        raw_message = message.as_bytes(
            policy=policy.SMTP,
        )

        append_status, _ = client.append(
            drafts_mailbox,
            r"(\Draft)",
            None,
            raw_message,
        )

        if not _status_is_ok(append_status):
            raise RuntimeError(
                "failed to save draft"
            )

        return drafts_mailbox

    finally:
        try:
            client.logout()
        except Exception:
            pass