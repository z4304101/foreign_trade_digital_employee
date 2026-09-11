from mail_reader.config import load_mail_config


def test_can_login_to_real_imap_mailbox():
    from mail_reader.imap_client import verify_imap_login

    config = load_mail_config()

    assert verify_imap_login(config) is True