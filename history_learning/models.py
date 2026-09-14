from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class HistoricalEmail:
    message_id: str
    mailbox: str
    direction: str
    sender: str
    recipients: str
    subject: str
    sent_at: datetime
    body: str
    customer_email: str
    customer_name: str = ""
    company_name: str = ""
    company_domain: str = ""


@dataclass
class StyleProfile:
    preferred_tone: str = ""
    typical_length: str = ""
    greeting_pattern: str = ""
    closing_pattern: str = ""
    structure_preferences: str = ""
    wording_preferences: str = ""
    manual_overrides: dict[str, str] = field(
        default_factory=dict
    )
    updated_at: str = ""


@dataclass(frozen=True)
class LearningSummary:
    scanned: int
    learned: int
    skipped: int
    failed: int
    sent_mailbox_found: bool
    style_profile_updated: bool
    warning: str = ""
