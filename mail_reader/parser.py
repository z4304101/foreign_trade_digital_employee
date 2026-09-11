from dataclasses import dataclass
from email import policy
from email.parser import BytesParser


@dataclass(frozen=True)
class ParsedEmail:
    sender: str
    subject: str
    date: str
    body: str


def parse_email(raw_email: bytes) -> ParsedEmail:
    message = BytesParser(policy=policy.default).parsebytes(raw_email)

    sender = str(message.get("From", ""))
    subject = str(message.get("Subject", ""))
    date = str(message.get("Date", ""))

    body = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()

            if content_type == "text/plain" and disposition != "attachment":
                content = part.get_content()

                if isinstance(content, str):
                    body = content
                    break
    else:
        content = message.get_content()

        if isinstance(content, str):
            body = content

    return ParsedEmail(
        sender=sender,
        subject=subject,
        date=date,
        body=body.strip(),
    )