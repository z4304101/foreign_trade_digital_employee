import json

from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    MemoryCredentialStore,
)
from desktop.settings_store import SettingsStore


def test_configuration_persists_settings_but_never_secrets(
    tmp_path,
):
    from desktop.configuration import DesktopConfiguration

    settings_path = (
        tmp_path
        / "settings.json"
    )

    credentials = (
        MemoryCredentialStore()
    )

    config = DesktopConfiguration(
        settings_store=SettingsStore(
            settings_path
        ),
        credentials=credentials,
    )

    config.save_mail(
        email_user="sales@163.com",
        auth_code="mail-secret",
    )

    config.save_identity(
        name="Alice",
        title="Sales Manager",
        company="Example Co.",
    )

    config.save_ai(
        provider="siliconflow",
        model="deepseek-ai/DeepSeek-V3",
        base_url="https://api.example.com/v1",
        api_key="ai-secret",
    )

    config.save_wecom(
        webhook="https://example.invalid/webhook-secret"
    )

    raw = settings_path.read_text(
        encoding="utf-8"
    )

    assert "sales@163.com" in raw
    assert "Alice" in raw

    assert "mail-secret" not in raw
    assert "ai-secret" not in raw
    assert "webhook-secret" not in raw

    assert (
        credentials.get(
            EMAIL_AUTH_CODE
        )
        == "mail-secret"
    )

    assert (
        credentials.get(
            AI_API_KEY
        )
        == "ai-secret"
    )

    assert (
        credentials.get(
            WECOM_WEBHOOK
        )
        == (
            "https://example.invalid/"
            "webhook-secret"
        )
    )


def test_configuration_persists_and_verifies_admin_pin(
    tmp_path,
):
    from desktop.configuration import DesktopConfiguration

    settings_path = (
        tmp_path
        / "settings.json"
    )

    credentials = (
        MemoryCredentialStore()
    )

    config = DesktopConfiguration(
        settings_store=SettingsStore(
            settings_path
        ),
        credentials=credentials,
    )

    config.create_admin_pin(
        "246810"
    )

    assert (
        config.has_admin_pin()
        is True
    )

    assert (
        config.verify_admin_pin(
            "246810"
        )
        is True
    )

    assert (
        config.verify_admin_pin(
            "111111"
        )
        is False
    )

    if settings_path.exists():
        raw = settings_path.read_text(
            encoding="utf-8"
        )

        assert "246810" not in raw


def test_configuration_reports_ai_ready_only_when_complete(
    tmp_path,
):
    from desktop.configuration import DesktopConfiguration

    config = DesktopConfiguration(
        settings_store=SettingsStore(
            tmp_path
            / "settings.json"
        ),
        credentials=MemoryCredentialStore(),
    )

    assert (
        config.is_ai_configured()
        is False
    )

    config.save_ai(
        provider="siliconflow",
        model="deepseek-ai/DeepSeek-V3",
        base_url="https://api.example.com/v1",
        api_key="secret",
    )

    assert (
        config.is_ai_configured()
        is True
    )


def test_configuration_reloads_nonsecret_settings(
    tmp_path,
):
    from desktop.configuration import DesktopConfiguration

    settings_path = (
        tmp_path
        / "settings.json"
    )

    credentials = (
        MemoryCredentialStore()
    )

    first = DesktopConfiguration(
        settings_store=SettingsStore(
            settings_path
        ),
        credentials=credentials,
    )

    first.save_identity(
        name="Alice",
        title="Sales Manager",
        company="Example Co.",
    )

    second = DesktopConfiguration(
        settings_store=SettingsStore(
            settings_path
        ),
        credentials=credentials,
    )

    assert (
        second.settings.sender_name
        == "Alice"
    )

    assert (
        second.settings.sender_title
        == "Sales Manager"
    )

    assert (
        second.settings.sender_company
        == "Example Co."
    )
