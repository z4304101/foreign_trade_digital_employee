from email.message import EmailMessage
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


def _build_reply_subject(
    subject: str,
) -> str:
    """
    Build a reply subject without duplicating Re:.

    Examples:
        Request for Quotation
        ->
        Re: Request for Quotation

        Re: Request for Quotation
        ->
        Re: Request for Quotation
    """

    subject = subject.strip()

    if not subject:
        return "Re:"

    if subject.lower().startswith("re:"):
        return subject

    return f"Re: {subject}"


def _build_references(
    mail: ParsedEmail,
) -> str:
    """
    Build the References header for the reply.

    Existing References are preserved and the current
    Message-ID is appended.
    """

    references = mail.references.strip()
    message_id = mail.message_id.strip()

    if references and message_id:
        return f"{references} {message_id}"

    if message_id:
        return message_id

    return references


def build_reply_message(
    mail: ParsedEmail,
    sender_email: str,
    reply_body: str,
) -> EmailMessage:
    """
    Build a MIME email reply suitable for saving as a draft.

    The message preserves email-thread metadata using:

    - Subject: Re: ...
    - In-Reply-To
    - References

    It does NOT send the email.
    """

    if not sender_email or not sender_email.strip():
        raise ValueError(
            "sender_email must not be empty"
        )

    if not isinstance(reply_body, str) or not reply_body.strip():
        raise ValueError(
            "reply_body must not be empty"
        )

    recipient = get_reply_recipient(mail)

    message = EmailMessage()

    message["From"] = sender_email.strip()
    message["To"] = recipient
    message["Subject"] = _build_reply_subject(
        mail.subject
    )

    message_id = mail.message_id.strip()

    if message_id:
        message["In-Reply-To"] = message_id

    references = _build_references(mail)

    if references:
        message["References"] = references

    message.set_content(
        reply_body.strip()
    )

    return message