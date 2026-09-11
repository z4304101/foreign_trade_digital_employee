from mail_reader.config import load_mail_config


def test_can_fetch_latest_raw_email_without_modifying_mailbox():
    from mail_reader.imap_client import fetch_latest_raw_email

    config = load_mail_config()

    raw_email = fetch_latest_raw_email(config)

    assert isinstance(raw_email, bytes)
    assert len(raw_email) > 0