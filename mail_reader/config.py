import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class MailConfig:
    email_user: str
    auth_code: str
    imap_host: str
    imap_port: int

    sender_name: str = ""
    sender_title: str = ""
    sender_company: str = ""


def load_mail_config() -> MailConfig:
    load_dotenv()

    email_user = os.getenv(
        "EMAIL_USER"
    )

    auth_code = os.getenv(
        "EMAIL_AUTH_CODE"
    )

    imap_host = os.getenv(
        "EMAIL_IMAP_HOST"
    )

    imap_port = os.getenv(
        "EMAIL_IMAP_PORT"
    )

    sender_name = os.getenv(
        "SENDER_NAME",
        "",
    )

    sender_title = os.getenv(
        "SENDER_TITLE",
        "",
    )

    sender_company = os.getenv(
        "SENDER_COMPANY",
        "",
    )

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
        sender_name=sender_name,
        sender_title=sender_title,
        sender_company=sender_company,
    )