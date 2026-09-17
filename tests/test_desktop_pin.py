import os

import pytest

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from desktop.credentials import MemoryCredentialStore


def test_admin_pin_requires_exactly_six_digits():
    from desktop.pin import AdminPin

    pin = AdminPin(
        MemoryCredentialStore()
    )

    invalid_values = (
        "",
        "12345",
        "1234567",
        "12a456",
        "abcdef",
        "123 56",
    )

    for value in invalid_values:
        with pytest.raises(ValueError):
            pin.set_pin(value)


def test_admin_pin_is_hashed_and_verified():
    from desktop.pin import (
        ADMIN_PIN_VERIFIER,
        AdminPin,
    )

    store = MemoryCredentialStore()

    pin = AdminPin(
        store
    )

    pin.set_pin(
        "246810"
    )

    stored = store.get(
        ADMIN_PIN_VERIFIER
    )

    assert stored is not None

    assert "246810" not in stored

    assert pin.has_pin() is True

    assert pin.verify_pin(
        "246810"
    ) is True

    assert pin.verify_pin(
        "111111"
    ) is False

    assert pin.verify_pin(
        "Secret123"
    ) is False


def test_same_pin_uses_different_salts():
    from desktop.pin import (
        ADMIN_PIN_VERIFIER,
        AdminPin,
    )

    first_store = MemoryCredentialStore()
    second_store = MemoryCredentialStore()

    first = AdminPin(
        first_store
    )

    second = AdminPin(
        second_store
    )

    first.set_pin(
        "246810"
    )

    second.set_pin(
        "246810"
    )

    assert (
        first_store.get(
            ADMIN_PIN_VERIFIER
        )
        != second_store.get(
            ADMIN_PIN_VERIFIER
        )
    )


def test_admin_pin_setup_dialog_requires_matching_six_digit_pin():
    from desktop.ui.admin_pin_setup_dialog import (
        AdminPinSetupDialog,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    created = []

    dialog = AdminPinSetupDialog(
        on_create=lambda value: (
            created.append(
                value
            )
        ),
    )

    assert (
        dialog.create_button.isEnabled()
        is False
    )

    dialog.pin_edit.setText(
        "123456"
    )

    dialog.confirm_pin_edit.setText(
        "654321"
    )

    assert (
        dialog.create_button.isEnabled()
        is False
    )

    assert (
        dialog.status_label.text()
        == "两次输入的 PIN 不一致"
    )

    dialog.confirm_pin_edit.setText(
        "123456"
    )

    assert (
        dialog.create_button.isEnabled()
        is True
    )

    dialog.create_button.click()

    assert created == [
        "123456",
    ]


def test_admin_unlock_dialog_uses_six_digit_pin():
    from desktop.ui.admin_unlock_dialog import (
        AdminUnlockDialog,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    unlocked = []

    dialog = AdminUnlockDialog(
        on_verify=lambda value: (
            value == "246810"
        ),
        on_unlocked=lambda: (
            unlocked.append(
                "yes"
            )
        ),
    )

    assert (
        dialog.pin_edit.maxLength()
        == 6
    )

    dialog.pin_edit.setText(
        "111111"
    )

    dialog.unlock_button.click()

    assert (
        dialog.status_label.text()
        == "管理员 PIN 错误"
    )

    assert unlocked == []

    dialog.pin_edit.setText(
        "246810"
    )

    dialog.unlock_button.click()

    assert unlocked == [
        "yes",
    ]


def test_onboarding_includes_pin_before_history_learning():
    from desktop.ui.onboarding_window import OnboardingWindow

    app = (
        QApplication.instance()
        or QApplication([])
    )

    created = []

    class Summary:
        failed = 0

    window = OnboardingWindow(
        on_test_mail=lambda email, auth: True,
        on_save_identity=lambda name, title, company: None,
        is_ai_configured=lambda: True,
        on_test_wecom=lambda webhook: True,
        on_create_pin=lambda value: created.append(value),
        on_learn_history=lambda: Summary(),
        on_complete=lambda: None,
    )

    assert window.STEP_NAMES == (
        "邮箱",
        "身份",
        "管理员 PIN",
        "AI",
        "企业微信",
        "学习",
    )

    window.stack.setCurrentIndex(2)

    assert (
        window.pin_next_button.isEnabled()
        is False
    )

    window.pin_edit.setText(
        "246810"
    )

    window.confirm_pin_edit.setText(
        "111111"
    )

    assert (
        window.pin_next_button.isEnabled()
        is False
    )

    assert (
        window.pin_status_label.text()
        == "两次输入的 PIN 不一致"
    )

    window.confirm_pin_edit.setText(
        "246810"
    )

    assert (
        window.pin_next_button.isEnabled()
        is True
    )

    window.pin_next_button.click()

    assert created == [
        "246810",
    ]

    assert (
        window.stack.currentIndex()
        == 3
    )

    window.close()


def test_onboarding_places_pin_before_ai_and_exposes_admin_ai_configuration():
    from desktop.ui.onboarding_window import OnboardingWindow

    app = (
        QApplication.instance()
        or QApplication([])
    )

    configured = {
        "value": False,
    }

    calls = []

    class Summary:
        failed = 0

    def configure_ai():
        calls.append("configure_ai")
        configured["value"] = True

    window = OnboardingWindow(
        on_test_mail=lambda email, auth: True,
        on_save_identity=lambda name, title, company: None,
        is_ai_configured=lambda: configured["value"],
        on_test_wecom=lambda webhook: True,
        on_create_pin=lambda value: None,
        on_configure_ai=configure_ai,
        on_learn_history=lambda: Summary(),
        on_complete=lambda: None,
    )

    assert window.STEP_NAMES == (
        "邮箱",
        "身份",
        "管理员 PIN",
        "AI",
        "企业微信",
        "学习",
    )

    window.stack.setCurrentIndex(3)

    assert window.ai_next_button.isEnabled() is False

    window.configure_ai_button.click()

    assert calls == [
        "configure_ai",
    ]

    assert (
        window.ai_status_label.text()
        == "AI 服务已配置"
    )

    assert (
        window.ai_next_button.isEnabled()
        is True
    )

    window.close()


def test_onboarding_back_navigation_matches_new_step_order():
    from PySide6.QtWidgets import QPushButton

    from desktop.ui.onboarding_window import OnboardingWindow

    app = (
        QApplication.instance()
        or QApplication([])
    )

    class Summary:
        failed = 0

    window = OnboardingWindow(
        on_test_mail=lambda email, auth: True,
        on_save_identity=lambda name, title, company: None,
        is_ai_configured=lambda: True,
        on_test_wecom=lambda webhook: True,
        on_create_pin=lambda value: None,
        on_configure_ai=lambda: None,
        on_learn_history=lambda: Summary(),
        on_complete=lambda: None,
    )

    def find_button(page, text):
        return next(
            button
            for button in page.findChildren(QPushButton)
            if button.text() == text
        )

    #
    # AI is step index 3.
    # Its back button must return to PIN index 2.
    #
    window.stack.setCurrentIndex(3)

    ai_back = find_button(
        window.stack.currentWidget(),
        "上一步",
    )

    ai_back.click()

    assert (
        window.stack.currentIndex()
        == 2
    )

    #
    # WeCom is step index 4.
    # Its back button must return to AI index 3.
    #
    window.stack.setCurrentIndex(4)

    wecom_back = find_button(
        window.stack.currentWidget(),
        "上一步",
    )

    wecom_back.click()

    assert (
        window.stack.currentIndex()
        == 3
    )

    window.close()
