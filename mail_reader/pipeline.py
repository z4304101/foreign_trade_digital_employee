from mail_reader.config import MailConfig
from mail_reader.imap_client import fetch_latest_raw_email
from mail_reader.parser import ParsedEmail, parse_email


def read_latest_email(config: MailConfig) -> ParsedEmail:
    raw_email = fetch_latest_raw_email(config)
    return parse_email(raw_email)