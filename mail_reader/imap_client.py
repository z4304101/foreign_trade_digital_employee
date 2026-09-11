import imaplib

from mail_reader.config import MailConfig


# Python imaplib does not register the IMAP ID extension
# by default, so register it for the AUTH state.
if "ID" not in imaplib.Commands:
    imaplib.Commands["ID"] = ("AUTH",)


def _send_client_id(
    client: imaplib.IMAP4_SSL,
) -> None:
    """
    Send IMAP ID information after login.

    163 Mail may reject mailbox access with
    "Unsafe Login" if the client does not send
    the IMAP ID command before selecting INBOX.
    """

    status, data = client._simple_command(
        "ID",
        '("name" "foreign-trade-digital-employee" '
        '"version" "0.3" '
        '"vendor" "local")',
    )

    if status != "OK":
        raise RuntimeError(
            f"Unable to send IMAP client ID: {data}"
        )


def verify_imap_login(
    config: MailConfig,
) -> bool:
    """
    Verify that the configured mailbox can log in
    and accept the IMAP ID command.
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

        return True

    finally:
        try:
            client.logout()
        except Exception:
            pass


def fetch_latest_raw_email(
    config: MailConfig,
) -> bytes:
    """
    Fetch the latest email from INBOX
    without modifying its read/unread state.
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

        # Required by providers such as 163 Mail.
        _send_client_id(
            client
        )

        status, _ = client.select(
            "INBOX",
            readonly=True,
        )

        if status != "OK":
            raise RuntimeError(
                "Unable to open INBOX in read-only mode"
            )

        status, data = client.search(
            None,
            "ALL",
        )

        if status != "OK":
            raise RuntimeError(
                "Unable to search mailbox"
            )

        if not data or not data[0]:
            raise RuntimeError(
                "Mailbox is empty"
            )

        message_ids = data[0].split()

        if not message_ids:
            raise RuntimeError(
                "Mailbox is empty"
            )

        latest_id = message_ids[-1]

        status, message_data = client.fetch(
            latest_id,
            "(BODY.PEEK[])",
        )

        if status != "OK":
            raise RuntimeError(
                "Unable to fetch latest email"
            )

        for item in message_data:
            if (
                isinstance(item, tuple)
                and len(item) >= 2
                and isinstance(item[1], bytes)
            ):
                return item[1]

        raise RuntimeError(
            "Email body was not returned"
        )

    finally:
        try:
            client.logout()
        except Exception:
            pass


def fetch_recent_raw_emails(
    config: MailConfig,
    limit: int = 20,
) -> list[bytes]:
    """
    Fetch multiple recent raw emails from INBOX.

    Emails are returned oldest -> newest
    within the selected recent window.

    Example:

        INBOX:
            101
            102
            103
            104

        limit=2

        returns:
            103
            104

    This function opens INBOX in read-only mode
    and does not intentionally change email flags.
    """

    if limit <= 0:
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

        # Important for real 163 Mail.
        # Without this, SELECT may fail with:
        # "EXAMINE Unsafe Login".
        _send_client_id(
            client
        )

        status, _ = client.select(
            "INBOX",
            readonly=True,
        )

        if status != "OK":
            raise RuntimeError(
                "Unable to open INBOX in read-only mode"
            )

        status, data = client.search(
            None,
            "ALL",
        )

        if status != "OK":
            raise RuntimeError(
                "Unable to search mailbox"
            )

        if not data or not data[0]:
            return []

        message_ids = data[0].split()

        if not message_ids:
            return []

        message_ids = message_ids[
            -limit:
        ]

        raw_emails: list[bytes] = []

        for message_id in message_ids:
            status, message_data = client.fetch(
                message_id,
                "(RFC822)",
            )

            if status != "OK":
                raise RuntimeError(
                    f"Unable to fetch email: "
                    f"{message_id!r}"
                )

            raw_email = None

            for item in message_data:
                if (
                    isinstance(item, tuple)
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
                    f"Email body was not returned: "
                    f"{message_id!r}"
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