from copy import deepcopy

from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    CredentialStore,
)
from desktop.models import (
    DesktopSettings,
)
from desktop.pin import AdminPin
from desktop.settings_store import (
    SettingsStore,
)


class DesktopConfiguration:
    """
    Single persistence boundary for the desktop app.

    Non-secret values:
        SettingsStore

    Secrets:
        CredentialStore

    Administrator PIN:
        hashed verifier through CredentialStore
    """

    def __init__(
        self,
        *,
        settings_store: SettingsStore,
        credentials: CredentialStore,
    ) -> None:
        self.settings_store = (
            settings_store
        )

        self.credentials = (
            credentials
        )

        self.settings = (
            self.settings_store.load()
        )

        self.admin_pin = AdminPin(
            credentials
        )

    def reload(
        self,
    ) -> DesktopSettings:
        self.settings = (
            self.settings_store.load()
        )

        return self.settings

    def save_settings(
        self,
        settings: DesktopSettings,
    ) -> None:
        self.settings = deepcopy(
            settings
        )

        self.settings_store.save(
            self.settings
        )

    def _update_settings(
        self,
        **changes,
    ) -> None:
        updated = deepcopy(
            self.settings
        )

        for key, value in (
            changes.items()
        ):
            setattr(
                updated,
                key,
                value,
            )

        self.save_settings(
            updated
        )

    def save_mail(
        self,
        *,
        email_user: str,
        auth_code: str,
    ) -> None:
        self._update_settings(
            email_user=(
                email_user.strip()
            )
        )

        if auth_code:
            self.credentials.set(
                EMAIL_AUTH_CODE,
                auth_code,
            )

    def save_identity(
        self,
        *,
        name: str,
        title: str,
        company: str,
    ) -> None:
        self._update_settings(
            sender_name=name.strip(),
            sender_title=title.strip(),
            sender_company=company.strip(),
        )

    def create_admin_pin(
        self,
        value: str,
    ) -> None:
        self.admin_pin.set_pin(
            value
        )

    def has_admin_pin(
        self,
    ) -> bool:
        return (
            self.admin_pin.has_pin()
        )

    def verify_admin_pin(
        self,
        value: str,
    ) -> bool:
        return (
            self.admin_pin.verify_pin(
                value
            )
        )

    def save_ai(
        self,
        *,
        provider: str,
        model: str,
        base_url: str,
        api_key: str = "",
    ) -> None:
        self._update_settings(
            llm_provider=(
                provider.strip()
            ),
            llm_model=(
                model.strip()
            ),
            llm_base_url=(
                base_url.strip()
            ),
        )

        if api_key:
            self.credentials.set(
                AI_API_KEY,
                api_key,
            )

    def is_ai_configured(
        self,
    ) -> bool:
        api_key = (
            self.credentials.get(
                AI_API_KEY
            )
            or ""
        )

        return all(
            (
                bool(
                    self.settings.llm_provider.strip()
                ),
                bool(
                    self.settings.llm_model.strip()
                ),
                bool(
                    self.settings.llm_base_url.strip()
                ),
                bool(
                    api_key.strip()
                ),
            )
        )

    def save_wecom(
        self,
        *,
        webhook: str,
    ) -> None:
        webhook = webhook.strip()

        if webhook:
            self.credentials.set(
                WECOM_WEBHOOK,
                webhook,
            )

        self._update_settings(
            wecom_enabled=bool(
                webhook
                or self.credentials.get(
                    WECOM_WEBHOOK
                )
            )
        )

    def is_wecom_configured(
        self,
    ) -> bool:
        return bool(
            self.settings.wecom_enabled
            and self.credentials.get(
                WECOM_WEBHOOK
            )
        )
