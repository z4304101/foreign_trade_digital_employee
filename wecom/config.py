import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class WeComConfig:
    webhook_url: str
    enabled: bool


def load_wecom_config() -> WeComConfig:
    """
    Load optional WeCom notification configuration.

    If WECOM_WEBHOOK_URL is missing or empty,
    WeCom notifications are disabled.

    Email processing must still work normally.
    """

    load_dotenv()

    webhook_url = os.getenv(
        "WECOM_WEBHOOK_URL",
        "",
    ).strip()

    return WeComConfig(
        webhook_url=webhook_url,
        enabled=bool(webhook_url),
    )