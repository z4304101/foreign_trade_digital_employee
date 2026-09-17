from copy import deepcopy
from collections.abc import Callable

from desktop.configuration import (
    DesktopConfiguration,
)
from desktop.core_bridge import (
    DesktopCoreBridge,
)
from desktop.credentials import (
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    MemoryCredentialStore,
)
from desktop.paths import DesktopPaths


class DesktopSetupController:
    """
    Real callback layer between desktop UI and
    configuration/business services.

    Candidate credentials are tested in memory first.
    They are persisted only after successful validation.
    """

    def __init__(
        self,
        *,
        configuration: DesktopConfiguration,
        paths: DesktopPaths,
        onboarding_service,
        bridge_factory: Callable = (
            DesktopCoreBridge
        ),
    ) -> None:
        self.configuration = (
            configuration
        )

        self.paths = paths

        self.onboarding_service = (
            onboarding_service
        )

        self.bridge_factory = (
            bridge_factory
        )

    def test_and_save_mail(
        self,
        email_user: str,
        auth_code: str,
    ) -> bool:
        email_user = (
            email_user.strip()
        )

        if (
            not email_user
            or not auth_code
        ):
            return False

        candidate_settings = deepcopy(
            self.configuration.settings
        )

        candidate_settings.email_user = (
            email_user
        )

        candidate_credentials = (
            MemoryCredentialStore()
        )

        candidate_credentials.set(
            EMAIL_AUTH_CODE,
            auth_code,
        )

        bridge = self.bridge_factory(
            settings=candidate_settings,
            credentials=(
                candidate_credentials
            ),
            paths=self.paths,
        )

        try:
            success = bool(
                bridge.verify_mail()
            )
        except Exception:
            success = False

        if not success:
            return False

        self.configuration.save_mail(
            email_user=email_user,
            auth_code=auth_code,
        )

        return True

    def save_identity(
        self,
        name: str,
        title: str,
        company: str,
    ) -> None:
        self.configuration.save_identity(
            name=name,
            title=title,
            company=company,
        )

    def create_admin_pin(
        self,
        value: str,
    ) -> None:
        self.configuration.create_admin_pin(
            value
        )

    def verify_admin_pin(
        self,
        value: str,
    ) -> bool:
        return (
            self.configuration.verify_admin_pin(
                value
            )
        )

    def is_ai_configured(
        self,
    ) -> bool:
        return (
            self.configuration.is_ai_configured()
        )

    def test_and_save_wecom(
        self,
        webhook: str,
    ) -> bool:
        webhook = webhook.strip()

        if not webhook:
            return False

        candidate_settings = deepcopy(
            self.configuration.settings
        )

        candidate_settings.wecom_enabled = (
            True
        )

        candidate_credentials = (
            MemoryCredentialStore()
        )

        candidate_credentials.set(
            WECOM_WEBHOOK,
            webhook,
        )

        bridge = self.bridge_factory(
            settings=candidate_settings,
            credentials=(
                candidate_credentials
            ),
            paths=self.paths,
        )

        try:
            success = bool(
                bridge.test_wecom()
            )
        except Exception:
            success = False

        if not success:
            return False

        self.configuration.save_wecom(
            webhook=webhook
        )

        return True

    def save_advanced_settings(
        self,
        settings,
    ) -> None:
        self.configuration.save_settings(
            settings
        )

    def learn_history(
        self,
    ):
        if self.onboarding_service is None:
            raise RuntimeError(
                "onboarding service is not configured"
            )

        summary = (
            self.onboarding_service
            .run_initial_history_learning()
        )

        self.configuration.reload()

        return summary

    def is_ready_for_production(
        self,
    ) -> bool:
        if self.onboarding_service is None:
            return False

        return bool(
            self.onboarding_service
            .is_ready_for_production()
        )
