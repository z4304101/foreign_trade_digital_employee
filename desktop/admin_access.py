"""
Compatibility layer for code written before the desktop
administrator credential was standardized on a six-digit PIN.

There is only one administrator credential implementation:
desktop.pin.AdminPin.
"""

from desktop.pin import (
    ADMIN_PIN_VERIFIER,
    AdminPin,
)


ADMIN_PASSWORD_VERIFIER = ADMIN_PIN_VERIFIER


class AdminAccess(AdminPin):
    """
    Backward-compatible name.

    New code must use AdminPin / set_pin / verify_pin.
    """

    def has_password(
        self,
    ) -> bool:
        return self.has_pin()

    def set_password(
        self,
        value: str,
    ) -> None:
        self.set_pin(
            value
        )

    def verify_password(
        self,
        value: str,
    ) -> bool:
        return self.verify_pin(
            value
        )
