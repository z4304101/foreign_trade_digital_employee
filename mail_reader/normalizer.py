import re
from dataclasses import dataclass

from mail_reader.parser import ParsedEmail


@dataclass(frozen=True)
class NormalizedEmail:
    sender: str
    subject: str
    date: str
    current_body: str
    previous_thread: str


QUOTE_PATTERNS = [
    r'\n在\s+\d{4}-\d{2}-\d{2}.*?写道：',
    r'\nOn\s+.+?\s+wrote:\s*',
    r'\n-{2,}\s*Original Message\s*-{2,}',
]


def normalize_email(mail: ParsedEmail) -> NormalizedEmail:
    body = mail.body.strip()

    split_index = None

    for pattern in QUOTE_PATTERNS:
        match = re.search(
            pattern,
            body,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            if split_index is None or match.start() < split_index:
                split_index = match.start()

    if split_index is None:
        current_body = body
        previous_thread = ""
    else:
        current_body = body[:split_index].strip()
        previous_thread = body[split_index:].strip()

    return NormalizedEmail(
        sender=mail.sender,
        subject=mail.subject,
        date=mail.date,
        current_body=current_body,
        previous_thread=previous_thread,
    )