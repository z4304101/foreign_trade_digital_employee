import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class MailConfig:
    email_user: str
    auth_code: str
    imap_host: str
    imap_port: int


def load_mail_config() -> MailConfig:
    load_dotenv()

    email_user = os.getenv("EMAIL_USER")
    auth_code = os.getenv("EMAIL_AUTH_CODE")
    imap_host = os.getenv("EMAIL_IMAP_HOST")
    imap_port = os.getenv("EMAIL_IMAP_PORT")

    missing = [
        name
        for name, value in {
            "EMAIL_USER": email_user,
            "EMAIL_AUTH_CODE": auth_code,
            "EMAIL_IMAP_HOST": imap_host,
            "EMAIL_IMAP_PORT": imap_port,
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )

    return MailConfig(
        email_user=email_user,
        auth_code=auth_code,
        imap_host=imap_host,
        imap_port=int(imap_port),
    )