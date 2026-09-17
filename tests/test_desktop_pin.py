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
