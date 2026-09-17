from desktop.admin_access import (
    ADMIN_PASSWORD_VERIFIER,
    AdminAccess,
)
from desktop.credentials import MemoryCredentialStore
from desktop.pin import ADMIN_PIN_VERIFIER


def test_legacy_admin_access_uses_the_same_pin_backend():
    assert (
        ADMIN_PASSWORD_VERIFIER
        == ADMIN_PIN_VERIFIER
    )

    store = MemoryCredentialStore()

    access = AdminAccess(
        store
    )

    access.set_password(
        "246810"
    )

    assert access.has_password() is True

    assert access.verify_password(
        "246810"
    ) is True

    assert access.verify_password(
        "111111"
    ) is False
