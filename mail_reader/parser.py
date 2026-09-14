from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser


@dataclass
class ParsedEmail:
    sender: str
    subject: str
    date: str
    body: str
    reply_to: str = ""
    message_id: str = ""
    references: str = ""
    recipients: str = ""


def _get_text_body(message: Message) -> str:
    """
    Extract the readable text body from an email.

    Priority:
    1. text/plain
    2. text/html as fallback

    Attachments are ignored.
    """

    if message.is_multipart():
        plain_text = ""
        html_text = ""

        for part in message.walk():
            content_disposition = (
                part.get_content_disposition()
            )

            if content_disposition == "attachment":
                continue

            content_type = part.get_content_type()

            if (
                content_type == "text/plain"
                and not plain_text
            ):
                try:
                    plain_text = part.get_content()
                except Exception:
                    payload = part.get_payload(
                        decode=True
                    )

                    if payload:
                        charset = (
                            part.get_content_charset()
                            or "utf-8"
                        )

                        plain_text = payload.decode(
                            charset,
                            errors="replace",
                        )

            elif (
                content_type == "text/html"
                and not html_text
            ):
                try:
                    html_text = part.get_content()
                except Exception:
                    payload = part.get_payload(
                        decode=True
                    )

                    if payload:
                        charset = (
                            part.get_content_charset()
                            or "utf-8"
                        )

                        html_text = payload.decode(
                            charset,
                            errors="replace",
                        )

        if plain_text:
            return plain_text.strip()

        if html_text:
            return html_text.strip()

        return ""

    try:
        content = message.get_content()

        if isinstance(content, str):
            return content.strip()

    except Exception:
        pass

    payload = message.get_payload(
        decode=True
    )

    if payload:
        charset = (
            message.get_content_charset()
            or "utf-8"
        )

        return payload.decode(
            charset,
            errors="replace",
        ).strip()

    payload = message.get_payload()

    if isinstance(payload, str):
        return payload.strip()

    return ""


def parse_email(
    raw_email: bytes,
) -> ParsedEmail:
    """
    Parse a raw RFC email message.

    Besides the normal email content, preserve
    metadata required for reply creation and
    historical learning:

    - To
    - Reply-To
    - Message-ID
    - References
    """

    if not isinstance(
        raw_email,
        bytes,
    ):
        raise TypeError(
            "raw_email must be bytes"
        )

    message = BytesParser(
        policy=policy.default,
    ).parsebytes(
        raw_email
    )

    sender = str(
        message.get(
            "From",
            "",
        )
    ).strip()

    recipients = str(
        message.get(
            "To",
            "",
        )
    ).strip()

    subject = str(
        message.get(
            "Subject",
            "",
        )
    ).strip()

    date = str(
        message.get(
            "Date",
            "",
        )
    ).strip()

    reply_to = str(
        message.get(
            "Reply-To",
            "",
        )
    ).strip()

    message_id = str(
        message.get(
            "Message-ID",
            "",
        )
    ).strip()

    references = str(
        message.get(
            "References",
            "",
        )
    ).strip()

    body = _get_text_body(
        message
    )

    return ParsedEmail(
        sender=sender,
        subject=subject,
        date=date,
        body=body,
        reply_to=reply_to,
        message_id=message_id,
        references=references,
        recipients=recipients,
    )
