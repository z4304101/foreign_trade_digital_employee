import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from desktop.credentials import MemoryCredentialStore


def test_admin_password_is_hashed_and_verified():
    from desktop.admin_access import (
        ADMIN_PASSWORD_VERIFIER,
        AdminAccess,
    )

    store = MemoryCredentialStore()

    access = AdminAccess(
        store
    )

    access.set_password(
        "Secret123"
    )

    stored = store.get(
        ADMIN_PASSWORD_VERIFIER
    )

    assert stored is not None

    assert (
        "Secret123"
        not in stored
    )

    assert access.verify_password(
        "Secret123"
    ) is True

    assert access.verify_password(
        "wrong-password"
    ) is False


def test_same_password_uses_different_salts():
    from desktop.admin_access import (
        ADMIN_PASSWORD_VERIFIER,
        AdminAccess,
    )

    first_store = MemoryCredentialStore()
    second_store = MemoryCredentialStore()

    first = AdminAccess(
        first_store
    )

    second = AdminAccess(
        second_store
    )

    first.set_password(
        "Secret123"
    )

    second.set_password(
        "Secret123"
    )

    assert (
        first_store.get(
            ADMIN_PASSWORD_VERIFIER
        )
        != second_store.get(
            ADMIN_PASSWORD_VERIFIER
        )
    )


def test_admin_unlock_dialog_rejects_wrong_password_and_accepts_correct_one():
    from desktop.ui.admin_unlock_dialog import (
        AdminUnlockDialog,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    unlocked = []

    dialog = AdminUnlockDialog(
        on_verify=lambda password: (
            password == "246810"
        ),
        on_unlocked=lambda: (
            unlocked.append(
                "yes"
            )
        ),
    )

    dialog.password_edit.setText(
        "111111"
    )

    dialog.unlock_button.click()

    assert (
        dialog.status_label.text()
        == "管理员密码错误"
    )

    assert unlocked == []

    dialog.password_edit.setText(
        "246810"
    )

    dialog.unlock_button.click()

    assert unlocked == [
        "yes",
    ]
