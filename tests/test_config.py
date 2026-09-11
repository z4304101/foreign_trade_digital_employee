import os


def test_mail_config_can_be_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("EMAIL_USER", "test@example.com")
    monkeypatch.setenv("EMAIL_AUTH_CODE", "test-auth-code")
    monkeypatch.setenv("EMAIL_IMAP_HOST", "imap.example.com")
    monkeypatch.setenv("EMAIL_IMAP_PORT", "993")

    from mail_reader.config import load_mail_config

    config = load_mail_config()

    assert config.email_user == "test@example.com"
    assert config.auth_code == "test-auth-code"
    assert config.imap_host == "imap.example.com"
    assert config.imap_port == 993