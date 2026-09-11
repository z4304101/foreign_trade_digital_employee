from email.utils import parseaddr

from mail_reader.parser import ParsedEmail


def _extract_email_address(value: str) -> str:
    """
    Extract a plain email address from an RFC email header.

    Example:
        "Michael Brown <michael@customer.com>"
        ->
        "michael@customer.com"
    """

    if not value:
        return ""

    _, address = parseaddr(value)

    return address.strip()


def get_reply_recipient(
    mail: ParsedEmail,
) -> str:
    """
    Determine the recipient for a reply.

    Priority:
    1. Reply-To
    2. From

    The returned value is always the plain email address.
    """

    reply_to = _extract_email_address(
        mail.reply_to
    )

    if reply_to:
        return reply_to

    sender = _extract_email_address(
        mail.sender
    )

    if sender:
        return sender

    raise ValueError(
        "Cannot determine reply recipient"
    )