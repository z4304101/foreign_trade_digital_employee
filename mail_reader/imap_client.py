import imaplib

from mail_reader.config import MailConfig


if "ID" not in imaplib.Commands:
    imaplib.Commands["ID"] = ("AUTH",)


def _send_client_id(client: imaplib.IMAP4_SSL) -> None:
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


def verify_imap_login(config: MailConfig) -> bool:
    client = imaplib.IMAP4_SSL(
        host=config.imap_host,
        port=config.imap_port,
    )

    try:
        client.login(
            config.email_user,
            config.auth_code,
        )

        _send_client_id(client)

        return True

    finally:
        try:
            client.logout()
        except Exception:
            pass


def fetch_latest_raw_email(config: MailConfig) -> bytes:
    client = imaplib.IMAP4_SSL(
        host=config.imap_host,
        port=config.imap_port,
    )

    try:
        client.login(
            config.email_user,
            config.auth_code,
        )

        _send_client_id(client)

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
            if isinstance(item, tuple):
                raw_email = item[1]

                if isinstance(raw_email, bytes):
                    return raw_email

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
    Fetch recent raw emails from INBOX.

    The returned emails are ordered from oldest to newest
    within the selected recent window.

    Example:
        INBOX message ids:
            101, 102, 103, 104

        limit=2

        returns:
            103, 104
    """

    client = imaplib.IMAP4_SSL(
        config.imap_host,
        config.imap_port,
    )

    try:
        client.login(
            config.email_user,
            config.auth_code,
        )

        status, _ = client.select(
            "INBOX"
        )

        if status != "OK":
            raise RuntimeError(
                "Failed to select INBOX"
            )

        status, data = client.search(
            None,
            "ALL",
        )

        if status != "OK":
            raise RuntimeError(
                "Failed to search INBOX"
            )

        if not data or not data[0]:
            return []

        message_ids = data[0].split()

        if limit > 0:
            message_ids = message_ids[-limit:]
        else:
            return []

        raw_emails = []

        for message_id in message_ids:
            status, message_data = client.fetch(
                message_id,
                "(RFC822)",
            )

            if status != "OK":
                raise RuntimeError(
                    f"Failed to fetch email: "
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
                    f"Email content missing: "
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