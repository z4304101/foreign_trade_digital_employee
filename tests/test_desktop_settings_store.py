import json
from pathlib import Path

from desktop.models import DesktopSettings
from desktop.settings_store import SettingsStore


def test_settings_store_never_serializes_secrets(
    tmp_path: Path,
):
    store = SettingsStore(
        tmp_path / "settings.json"
    )

    settings = DesktopSettings(
        email_user="sales@163.com",
    )

    store.save(settings)

    raw = json.loads(
        (tmp_path / "settings.json").read_text(
            encoding="utf-8"
        )
    )

    assert raw["email_user"] == "sales@163.com"

    assert "auth_code" not in raw
    assert "api_key" not in raw
    assert "webhook" not in raw


def test_settings_store_returns_defaults_when_file_missing(
    tmp_path: Path,
):
    store = SettingsStore(
        tmp_path / "settings.json"
    )

    settings = store.load()

    assert settings.email_user == ""
    assert settings.imap_host == "imap.163.com"
    assert settings.imap_port == 993
    assert settings.poll_interval_seconds == 180
    assert settings.autostart_enabled is True
    assert settings.history_months == 6
    assert settings.history_limit == 1000
    assert settings.onboarding_completed is False
    assert settings.baseline_completed is False


def test_credentials_never_leak_into_settings_file(
    tmp_path: Path,
):
    from desktop.credentials import (
        AI_API_KEY,
        EMAIL_AUTH_CODE,
        WECOM_WEBHOOK,
        MemoryCredentialStore,
    )

    credential_store = MemoryCredentialStore()

    credential_store.set(
        EMAIL_AUTH_CODE,
        "mail-secret-value",
    )
    credential_store.set(
        AI_API_KEY,
        "ai-secret-value",
    )
    credential_store.set(
        WECOM_WEBHOOK,
        "https://example.invalid/secret-hook",
    )

    settings_store = SettingsStore(
        tmp_path / "settings.json"
    )

    settings_store.save(
        DesktopSettings(
            email_user="sales@163.com",
            llm_model="test-model",
        )
    )

    raw_text = (
        tmp_path / "settings.json"
    ).read_text(
        encoding="utf-8"
    )

    assert "mail-secret-value" not in raw_text
    assert "ai-secret-value" not in raw_text
    assert (
        "https://example.invalid/secret-hook"
        not in raw_text
    )

    assert (
        credential_store.get(EMAIL_AUTH_CODE)
        == "mail-secret-value"
    )
    assert (
        credential_store.get(AI_API_KEY)
        == "ai-secret-value"
    )
    assert (
        credential_store.get(WECOM_WEBHOOK)
        == "https://example.invalid/secret-hook"
    )
