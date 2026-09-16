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
