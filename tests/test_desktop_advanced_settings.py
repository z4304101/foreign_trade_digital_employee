import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from desktop.credentials import (
    AI_API_KEY,
    WECOM_WEBHOOK,
    MemoryCredentialStore,
)
from desktop.models import DesktopSettings


def test_advanced_settings_loads_technical_fields_without_exposing_existing_secrets():
    from desktop.ui.advanced_settings_dialog import (
        AdvancedSettingsDialog,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    credentials = MemoryCredentialStore()

    credentials.set(
        AI_API_KEY,
        "real-secret-key",
    )

    credentials.set(
        WECOM_WEBHOOK,
        "https://example.com/real-webhook",
    )

    settings = DesktopSettings(
        imap_host="imap.163.com",
        imap_port=993,
        llm_provider="siliconflow",
        llm_model="deepseek-ai/DeepSeek-V3",
        llm_base_url="https://api.siliconflow.cn/v1",
        poll_interval_seconds=180,
        history_months=6,
        history_limit=1000,
        log_level="INFO",
    )

    saved = []

    dialog = AdvancedSettingsDialog(
        settings=settings,
        credentials=credentials,
        on_save=lambda updated: saved.append(
            updated
        ),
    )

    assert dialog.imap_host_edit.text() == "imap.163.com"
    assert dialog.imap_port_spin.value() == 993

    assert dialog.provider_edit.text() == "siliconflow"

    assert (
        dialog.model_edit.text()
        == "deepseek-ai/DeepSeek-V3"
    )

    assert (
        dialog.base_url_edit.text()
        == "https://api.siliconflow.cn/v1"
    )

    #
    # Existing secrets must never be echoed back into UI.
    #
    assert dialog.api_key_edit.text() == ""
    assert dialog.webhook_edit.text() == ""

    assert dialog.poll_interval_spin.value() == 180
    assert dialog.history_months_spin.value() == 6
    assert dialog.history_limit_spin.value() == 1000
    assert dialog.log_level_combo.currentText() == "INFO"

    dialog.close()


def test_advanced_settings_updates_nonsecret_settings_and_new_secrets():
    from desktop.ui.advanced_settings_dialog import (
        AdvancedSettingsDialog,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    credentials = MemoryCredentialStore()

    settings = DesktopSettings()

    saved = []

    dialog = AdvancedSettingsDialog(
        settings=settings,
        credentials=credentials,
        on_save=lambda updated: saved.append(
            updated
        ),
    )

    dialog.provider_edit.setText(
        "siliconflow"
    )

    dialog.model_edit.setText(
        "deepseek-ai/DeepSeek-V3"
    )

    dialog.base_url_edit.setText(
        "https://api.siliconflow.cn/v1"
    )

    dialog.api_key_edit.setText(
        "new-api-key"
    )

    dialog.webhook_edit.setText(
        "https://example.com/new-webhook"
    )

    dialog.imap_host_edit.setText(
        "imap.163.com"
    )

    dialog.imap_port_spin.setValue(
        993
    )

    dialog.poll_interval_spin.setValue(
        240
    )

    dialog.history_months_spin.setValue(
        12
    )

    dialog.history_limit_spin.setValue(
        1500
    )

    dialog.log_level_combo.setCurrentText(
        "DEBUG"
    )

    dialog.save_button.click()

    assert len(saved) == 1

    updated = saved[0]

    assert updated.llm_provider == "siliconflow"
    assert updated.poll_interval_seconds == 240
    assert updated.history_months == 12
    assert updated.history_limit == 1500
    assert updated.log_level == "DEBUG"

    assert credentials.get(
        AI_API_KEY
    ) == "new-api-key"

    assert credentials.get(
        WECOM_WEBHOOK
    ) == "https://example.com/new-webhook"
