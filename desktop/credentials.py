from typing import Protocol

import keyring
from keyring.errors import PasswordDeleteError


SERVICE_NAME = "foreign-trade-digital-employee"

EMAIL_AUTH_CODE = "email_auth_code"
AI_API_KEY = "ai_api_key"
WECOM_WEBHOOK = "wecom_webhook"


class CredentialStore(Protocol):
    def get(
        self,
        key: str,
    ) -> str | None:
        ...

    def set(
        self,
        key: str,
        value: str,
    ) -> None:
        ...

    def delete(
        self,
        key: str,
    ) -> None:
        ...


class MemoryCredentialStore:
    """
    In-memory credential store used by tests.

    It must never be used as the production
    secret store.
    """

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get(
        self,
        key: str,
    ) -> str | None:
        return self._values.get(key)

    def set(
        self,
        key: str,
        value: str,
    ) -> None:
        self._values[key] = value

    def delete(
        self,
        key: str,
    ) -> None:
        self._values.pop(
            key,
            None,
        )


class KeyringCredentialStore:
    """
    Production credential store.

    macOS:
        keyring -> Keychain

    Windows:
        keyring -> Credential Manager
    """

    def __init__(
        self,
        service_name: str = SERVICE_NAME,
    ) -> None:
        self.service_name = service_name

    def get(
        self,
        key: str,
    ) -> str | None:
        return keyring.get_password(
            self.service_name,
            key,
        )

    def set(
        self,
        key: str,
        value: str,
    ) -> None:
        keyring.set_password(
            self.service_name,
            key,
            value,
        )

    def delete(
        self,
        key: str,
    ) -> None:
        try:
            keyring.delete_password(
                self.service_name,
                key,
            )
        except PasswordDeleteError:
            pass
