from mail_reader.config import MailConfig
from mail_reader.imap_client import (
    fetch_latest_raw_email,
    fetch_recent_raw_emails,
)
from mail_reader.parser import (
    ParsedEmail,
    parse_email,
)


def read_latest_email(
    config: MailConfig,
) -> ParsedEmail:
    """
    Fetch the latest raw email from INBOX
    and parse it into a ParsedEmail object.

    This function preserves the existing
    single-email workflow.
    """

    raw_email = fetch_latest_raw_email(
        config
    )

    return parse_email(
        raw_email
    )


def read_recent_emails(
    config: MailConfig,
    limit: int = 20,
) -> list[ParsedEmail]:
    """
    Fetch multiple recent emails from INBOX
    and parse each one into a ParsedEmail object.

    Emails remain in the same order returned by
    fetch_recent_raw_emails(), which is expected
    to be oldest -> newest within the selected window.

    Example:

        INBOX:
            message A
            message B
            message C

        read_recent_emails(...)

        returns:
            [
                ParsedEmail(A),
                ParsedEmail(B),
                ParsedEmail(C),
            ]

    If no email is available, return an empty list.
    """

    raw_emails = fetch_recent_raw_emails(
        config=config,
        limit=limit,
    )

    emails = []

    for raw_email in raw_emails:
        parsed_email = parse_email(
            raw_email
        )

        emails.append(
            parsed_email
        )

    return emails