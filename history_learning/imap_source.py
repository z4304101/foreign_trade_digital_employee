import imaplib
import re
from datetime import date

from mail_reader.config import MailConfig
from mail_reader.imap_client import _send_client_id


COMMON_SENT_NAMES = (
    "sent",
    "sent messages",
    "sent mail",
    "已发送",
    "已发送邮件",
)


def _decode_list_row(
    row: bytes | str,
) -> str:
    if isinstance(row, bytes):
        return row.decode(
            "utf-8",
            errors="replace",
        )

    return str(row)


def _extract_mailbox_name(
    row: bytes | str,
) -> str:
    """
    Extract the mailbox name from one IMAP LIST row.

    Typical examples:

        (\\HasNoChildren \\Sent) "/" "Sent"
        (\\HasNoChildren) "/" "Sent Messages"
    """

    text = _decode_list_row(
        row
    ).strip()

    quoted = re.findall(
        r'"([^"]*)"',
        text,
    )

    if quoted:
        return quoted[-1].strip()

    parts = text.split()

    if not parts:
        return ""

    return parts[-1].strip(
        '"'
    )


def discover_sent_mailbox(
    config: MailConfig,
) -> str | None:
    """
    Discover the mailbox representing sent mail.

    Priority:
    1. IMAP special-use \\Sent flag.
    2. Common Sent-folder names.

    This function only lists mailboxes.
    It does not modify any message.
    """

    client = imaplib.IMAP4_SSL(
        host=config.imap_host,
        port=config.imap_port,
    )

    try:
        client.login(
            config.email_user,
            config.auth_code,
        )

        _send_client_id(
            client
        )

        status, rows = client.list()

        if status != "OK":
            raise RuntimeError(
                "Unable to list IMAP mailboxes"
            )

        rows = rows or []

        # First choice:
        # trust the server's special-use Sent flag.
        for row in rows:
            text = _decode_list_row(
                row
            )

            if re.search(
                r"\\Sent(?:\s|\))",
                text,
                flags=re.IGNORECASE,
            ):
                mailbox = _extract_mailbox_name(
                    row
                )

                if mailbox:
                    return mailbox

        # Fallback:
        # use common localized/common Sent names.
        common_names = {
            name.lower()
            for name in COMMON_SENT_NAMES
        }

        for row in rows:
            mailbox = _extract_mailbox_name(
                row
            )

            if mailbox.lower() in common_names:
                return mailbox

        return None

    finally:
        try:
            client.logout()
        except Exception:
            pass


def fetch_folder_raw_emails(
    config: MailConfig,
    mailbox: str,
    since: date,
    max_messages: int = 1000,
) -> list[bytes]:
    """
    Read historical emails from a mailbox safely.

    Safety requirements:
    - mailbox is opened with readonly=True
    - messages are fetched using BODY.PEEK[]
    - no flags are intentionally changed
    - no message is moved, deleted, or sent
    """

    if max_messages <= 0:
        return []

    client = imaplib.IMAP4_SSL(
        host=config.imap_host,
        port=config.imap_port,
    )

    try:
        client.login(
            config.email_user,
            config.auth_code,
        )

        _send_client_id(
            client
        )

        status, _ = client.select(
            mailbox,
            readonly=True,
        )

        if status != "OK":
            raise RuntimeError(
                f"Unable to open mailbox "
                f"in read-only mode: {mailbox}"
            )

        status, data = client.search(
            None,
            "SINCE",
            since.strftime(
                "%d-%b-%Y"
            ),
        )

        if status != "OK":
            raise RuntimeError(
                f"Unable to search mailbox: "
                f"{mailbox}"
            )

        if not data or not data[0]:
            return []

        message_ids = data[0].split()

        if not message_ids:
            return []

        message_ids = message_ids[
            -max_messages:
        ]

        raw_emails: list[bytes] = []

        for message_id in message_ids:
            status, message_data = (
                client.fetch(
                    message_id,
                    "(BODY.PEEK[])",
                )
            )

            if status != "OK":
                raise RuntimeError(
                    "Unable to fetch historical "
                    f"email: {message_id!r}"
                )

            raw_email = None

            for item in message_data:
                if (
                    isinstance(
                        item,
                        tuple,
                    )
                    and len(item) >= 2
                    and isinstance(
                        item[1],
                        bytes,
                    )
                ):
                    raw_email = item[1]
                    break

            if raw_email is None:
                raise RuntimeError(
                    "Historical email body was "
                    f"not returned: {message_id!r}"
                )

            raw_emails.append(
                raw_email
            )

        return raw_emails

    finally:
        try:
            client.logout()
        except Exception:
            pass
