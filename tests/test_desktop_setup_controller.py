from pathlib import Path

from desktop.configuration import (
    DesktopConfiguration,
)
from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    MemoryCredentialStore,
)
from desktop.paths import DesktopPaths
from desktop.settings_store import SettingsStore


class Summary:
    failed = 0


def build_configuration(tmp_path):
    paths = DesktopPaths.from_root(
        tmp_path
    )

    paths.ensure()

    credentials = (
        MemoryCredentialStore()
    )

    settings_store = SettingsStore(
        paths.settings_file
    )

    configuration = DesktopConfiguration(
        settings_store=settings_store,
        credentials=credentials,
    )

    return (
        paths,
        credentials,
        settings_store,
        configuration,
    )


def test_mail_is_persisted_only_after_successful_verification(
    tmp_path,
):
    from desktop.setup_controller import (
        DesktopSetupController,
    )

    (
        paths,
        credentials,
        settings_store,
        configuration,
    ) = build_configuration(
        tmp_path
    )

    verified = {
        "value": False,
    }

    captured = {}

    class FakeBridge:
        def __init__(
            self,
            *,
            settings,
            credentials,
            paths,
        ):
            captured["settings"] = settings
            captured["credentials"] = credentials

        def verify_mail(self):
            return verified["value"]

    controller = DesktopSetupController(
        configuration=configuration,
        paths=paths,
        onboarding_service=None,
        bridge_factory=FakeBridge,
    )

    assert (
        controller.test_and_save_mail(
            "sales@163.com",
            "mail-secret",
        )
        is False
    )

    assert (
        settings_store.load().email_user
        == ""
    )

    assert (
        credentials.get(
            EMAIL_AUTH_CODE
        )
        is None
    )

    verified["value"] = True

    assert (
        controller.test_and_save_mail(
            "sales@163.com",
            "mail-secret",
        )
        is True
    )

    assert (
        settings_store.load().email_user
        == "sales@163.com"
    )

    assert (
        credentials.get(
            EMAIL_AUTH_CODE
        )
        == "mail-secret"
    )

    assert (
        captured[
            "settings"
        ].email_user
        == "sales@163.com"
    )

    assert (
        captured[
            "credentials"
        ].get(
            EMAIL_AUTH_CODE
        )
        == "mail-secret"
    )


def test_wecom_is_persisted_only_after_successful_test(
    tmp_path,
):
    from desktop.setup_controller import (
        DesktopSetupController,
    )

    (
        paths,
        credentials,
        settings_store,
        configuration,
    ) = build_configuration(
        tmp_path
    )

    verified = {
        "value": False,
    }

    class FakeBridge:
        def __init__(
            self,
            *,
            settings,
            credentials,
            paths,
        ):
            self.settings = settings
            self.credentials = credentials

        def test_wecom(self):
            return verified["value"]

    controller = DesktopSetupController(
        configuration=configuration,
        paths=paths,
        onboarding_service=None,
        bridge_factory=FakeBridge,
    )

    webhook = (
        "https://example.invalid/"
        "wecom-secret"
    )

    assert (
        controller.test_and_save_wecom(
            webhook
        )
        is False
    )

    assert (
        credentials.get(
            WECOM_WEBHOOK
        )
        is None
    )

    verified["value"] = True

    assert (
        controller.test_and_save_wecom(
            webhook
        )
        is True
    )

    assert (
        credentials.get(
            WECOM_WEBHOOK
        )
        == webhook
    )

    assert (
        settings_store.load().wecom_enabled
        is True
    )


def test_controller_delegates_identity_pin_and_ai_state(
    tmp_path,
):
    from desktop.setup_controller import (
        DesktopSetupController,
    )

    (
        paths,
        credentials,
        settings_store,
        configuration,
    ) = build_configuration(
        tmp_path
    )

    controller = DesktopSetupController(
        configuration=configuration,
        paths=paths,
        onboarding_service=None,
        bridge_factory=lambda **kwargs: None,
    )

    controller.save_identity(
        "Alice",
        "Sales Manager",
        "Example Co.",
    )

    saved = settings_store.load()

    assert saved.sender_name == "Alice"
    assert saved.sender_title == "Sales Manager"
    assert saved.sender_company == "Example Co."

    controller.create_admin_pin(
        "246810"
    )

    assert (
        controller.verify_admin_pin(
            "246810"
        )
        is True
    )

    assert (
        controller.verify_admin_pin(
            "111111"
        )
        is False
    )

    assert (
        controller.is_ai_configured()
        is False
    )

    configuration.save_ai(
        provider="siliconflow",
        model="test-model",
        base_url="https://api.example.invalid/v1",
        api_key="ai-secret",
    )

    assert (
        credentials.get(
            AI_API_KEY
        )
        == "ai-secret"
    )

    assert (
        controller.is_ai_configured()
        is True
    )


def test_history_learning_refreshes_cached_settings(
    tmp_path,
):
    from desktop.setup_controller import (
        DesktopSetupController,
    )

    (
        paths,
        credentials,
        settings_store,
        configuration,
    ) = build_configuration(
        tmp_path
    )

    class FakeOnboardingService:
        def run_initial_history_learning(
            self,
        ):
            settings = (
                settings_store.load()
            )

            settings.baseline_completed = True
            settings.onboarding_completed = True

            settings_store.save(
                settings
            )

            return Summary()

        def is_ready_for_production(
            self,
        ):
            settings = (
                settings_store.load()
            )

            return bool(
                settings.baseline_completed
                and settings.onboarding_completed
            )

    controller = DesktopSetupController(
        configuration=configuration,
        paths=paths,
        onboarding_service=(
            FakeOnboardingService()
        ),
        bridge_factory=lambda **kwargs: None,
    )

    summary = (
        controller.learn_history()
    )

    assert summary.failed == 0

    assert (
        configuration.settings.baseline_completed
        is True
    )

    assert (
        configuration.settings.onboarding_completed
        is True
    )

    assert (
        controller.is_ready_for_production()
        is True
    )
