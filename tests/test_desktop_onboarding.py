from pathlib import Path

from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    MemoryCredentialStore,
)
from desktop.models import DesktopSettings
from desktop.paths import DesktopPaths
from desktop.settings_store import SettingsStore

from desktop.onboarding import OnboardingService


def test_production_is_blocked_before_baseline_is_completed(
    tmp_path: Path,
):
    paths = DesktopPaths.from_root(
        tmp_path
    )
    paths.ensure()

    settings_store = SettingsStore(
        paths.settings_file
    )

    settings_store.save(
        DesktopSettings(
            email_user="sales@163.com",
            llm_provider="siliconflow",
            llm_model="test-model",
            llm_base_url="https://api.example.invalid/v1",
            wecom_enabled=True,
            onboarding_completed=True,
            baseline_completed=False,
        )
    )

    credentials = MemoryCredentialStore()

    credentials.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )

    credentials.set(
        AI_API_KEY,
        "ai-secret",
    )

    credentials.set(
        WECOM_WEBHOOK,
        "https://example.invalid/wecom-hook",
    )

    service = OnboardingService(
        settings_store=settings_store,
        credential_store=credentials,
        paths=paths,
        core_bridge_factory=lambda *args, **kwargs: None,
    )

    assert (
        service.is_ready_for_production()
        is False
    )


def test_production_is_ready_when_all_required_configuration_exists(
    tmp_path: Path,
):
    paths = DesktopPaths.from_root(
        tmp_path
    )
    paths.ensure()

    settings_store = SettingsStore(
        paths.settings_file
    )

    settings_store.save(
        DesktopSettings(
            email_user="sales@163.com",
            llm_provider="siliconflow",
            llm_model="test-model",
            llm_base_url="https://api.example.invalid/v1",
            wecom_enabled=True,
            onboarding_completed=True,
            baseline_completed=True,
        )
    )

    credentials = MemoryCredentialStore()

    credentials.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )
    credentials.set(
        AI_API_KEY,
        "ai-secret",
    )
    credentials.set(
        WECOM_WEBHOOK,
        "https://example.invalid/wecom-hook",
    )

    service = OnboardingService(
        settings_store=settings_store,
        credential_store=credentials,
        paths=paths,
        core_bridge_factory=lambda *args, **kwargs: None,
    )

    assert (
        service.is_ready_for_production()
        is True
    )


def test_wecom_webhook_is_not_required_when_wecom_is_disabled(
    tmp_path: Path,
):
    paths = DesktopPaths.from_root(
        tmp_path
    )
    paths.ensure()

    settings_store = SettingsStore(
        paths.settings_file
    )

    settings_store.save(
        DesktopSettings(
            email_user="sales@163.com",
            llm_provider="siliconflow",
            llm_model="test-model",
            llm_base_url="https://api.example.invalid/v1",
            wecom_enabled=False,
            onboarding_completed=True,
            baseline_completed=True,
        )
    )

    credentials = MemoryCredentialStore()

    credentials.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )
    credentials.set(
        AI_API_KEY,
        "ai-secret",
    )

    service = OnboardingService(
        settings_store=settings_store,
        credential_store=credentials,
        paths=paths,
        core_bridge_factory=lambda *args, **kwargs: None,
    )

    assert (
        service.is_ready_for_production()
        is True
    )


def test_history_learning_failure_does_not_open_production_gate(
    tmp_path: Path,
    monkeypatch,
):
    import pytest
    import desktop.onboarding as onboarding_module

    paths = DesktopPaths.from_root(
        tmp_path
    )
    paths.ensure()

    settings_store = SettingsStore(
        paths.settings_file
    )

    settings_store.save(
        DesktopSettings(
            email_user="sales@163.com",
            llm_provider="siliconflow",
            llm_model="test-model",
            llm_base_url="https://api.example.invalid/v1",
            wecom_enabled=True,
            onboarding_completed=False,
            baseline_completed=False,
        )
    )

    credentials = MemoryCredentialStore()

    credentials.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )
    credentials.set(
        AI_API_KEY,
        "ai-secret",
    )
    credentials.set(
        WECOM_WEBHOOK,
        "https://example.invalid/wecom-hook",
    )

    class FakeBridge:
        def build_mail_config(self):
            return object()

        def build_llm_config(self):
            return object()

    def fake_bridge_factory(
        *args,
        **kwargs,
    ):
        return FakeBridge()

    monkeypatch.setattr(
        onboarding_module,
        "create_llm_provider",
        lambda config: object(),
        raising=False,
    )

    def fake_run_initial_learning(
        **kwargs,
    ):
        raise RuntimeError(
            "history learning failed"
        )

    monkeypatch.setattr(
        onboarding_module,
        "run_initial_learning",
        fake_run_initial_learning,
        raising=False,
    )

    service = OnboardingService(
        settings_store=settings_store,
        credential_store=credentials,
        paths=paths,
        core_bridge_factory=fake_bridge_factory,
    )

    with pytest.raises(
        RuntimeError,
        match="history learning failed",
    ):
        service.run_initial_history_learning()

    saved = settings_store.load()

    assert saved.baseline_completed is False
    assert saved.onboarding_completed is False

    assert (
        service.is_ready_for_production()
        is False
    )


def test_successful_history_learning_opens_gate_only_after_real_baseline(
    tmp_path: Path,
    monkeypatch,
):
    from datetime import datetime, timezone

    import desktop.onboarding as onboarding_module

    from history_learning.models import (
        HistoricalEmail,
        LearningSummary,
    )
    from history_learning.store import (
        HistoryStore,
    )
    from mail_reader.processed_store import (
        is_message_processed,
    )

    paths = DesktopPaths.from_root(
        tmp_path
    )
    paths.ensure()

    settings_store = SettingsStore(
        paths.settings_file
    )

    settings_store.save(
        DesktopSettings(
            email_user="sales@163.com",
            llm_provider="siliconflow",
            llm_model="test-model",
            llm_base_url="https://api.example.invalid/v1",
            wecom_enabled=True,
            onboarding_completed=False,
            baseline_completed=False,
        )
    )

    credentials = MemoryCredentialStore()

    credentials.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )
    credentials.set(
        AI_API_KEY,
        "ai-secret",
    )
    credentials.set(
        WECOM_WEBHOOK,
        "https://example.invalid/wecom-hook",
    )

    class FakeBridge:
        def build_mail_config(self):
            return object()

        def build_llm_config(self):
            return object()

    def fake_bridge_factory(
        *args,
        **kwargs,
    ):
        return FakeBridge()

    monkeypatch.setattr(
        onboarding_module,
        "create_llm_provider",
        lambda config: object(),
    )

    historical_message_id = (
        "<historical-inquiry@example.com>"
    )

    def fake_run_initial_learning(
        *,
        mail_config,
        provider,
        db_path,
    ):
        store = HistoryStore(
            db_path
        )
        store.initialize()

        store.insert_email(
            HistoricalEmail(
                message_id=historical_message_id,
                mailbox="INBOX",
                direction="incoming",
                sender="customer@example.com",
                recipients="sales@163.com",
                subject="Old RFQ",
                sent_at=datetime(
                    2026,
                    8,
                    1,
                    10,
                    0,
                    tzinfo=timezone.utc,
                ),
                body="Historical inquiry",
                customer_email=(
                    "customer@example.com"
                ),
            )
        )

        store.set_learning_state(
            {
                "initial_learning_completed": "true",
            }
        )

        return LearningSummary(
            scanned=1,
            learned=1,
            skipped=0,
            failed=0,
            sent_mailbox_found=True,
            style_profile_updated=True,
        )

    monkeypatch.setattr(
        onboarding_module,
        "run_initial_learning",
        fake_run_initial_learning,
    )

    service = OnboardingService(
        settings_store=settings_store,
        credential_store=credentials,
        paths=paths,
        core_bridge_factory=fake_bridge_factory,
    )

    summary = (
        service.run_initial_history_learning()
    )

    assert summary.learned == 1
    assert summary.failed == 0

    saved = settings_store.load()

    assert saved.baseline_completed is True
    assert saved.onboarding_completed is True

    assert is_message_processed(
        message_id=historical_message_id,
        store_path=paths.processed_store,
    )

    assert (
        service.is_ready_for_production()
        is True
    )


def test_history_learning_with_failures_does_not_open_gate(
    tmp_path: Path,
    monkeypatch,
):
    import desktop.onboarding as onboarding_module

    from history_learning.models import (
        LearningSummary,
    )
    from history_learning.store import (
        HistoryStore,
    )

    paths = DesktopPaths.from_root(
        tmp_path
    )
    paths.ensure()

    settings_store = SettingsStore(
        paths.settings_file
    )

    settings_store.save(
        DesktopSettings(
            email_user="sales@163.com",
            llm_provider="siliconflow",
            llm_model="test-model",
            llm_base_url="https://api.example.invalid/v1",
            wecom_enabled=True,
            onboarding_completed=False,
            baseline_completed=False,
        )
    )

    credentials = MemoryCredentialStore()

    credentials.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )
    credentials.set(
        AI_API_KEY,
        "ai-secret",
    )
    credentials.set(
        WECOM_WEBHOOK,
        "https://example.invalid/wecom-hook",
    )

    class FakeBridge:
        def build_mail_config(self):
            return object()

        def build_llm_config(self):
            return object()

    monkeypatch.setattr(
        onboarding_module,
        "create_llm_provider",
        lambda config: object(),
    )

    def fake_run_initial_learning(
        *,
        mail_config,
        provider,
        db_path,
    ):
        store = HistoryStore(
            db_path
        )
        store.initialize()

        # Deliberately simulate an inconsistent state:
        # DB says completed, but this run had failures.
        store.set_learning_state(
            {
                "initial_learning_completed": "true",
            }
        )

        return LearningSummary(
            scanned=10,
            learned=8,
            skipped=1,
            failed=1,
            sent_mailbox_found=True,
            style_profile_updated=False,
            warning="one historical message failed",
        )

    monkeypatch.setattr(
        onboarding_module,
        "run_initial_learning",
        fake_run_initial_learning,
    )

    service = OnboardingService(
        settings_store=settings_store,
        credential_store=credentials,
        paths=paths,
        core_bridge_factory=lambda *args, **kwargs: FakeBridge(),
    )

    summary = (
        service.run_initial_history_learning()
    )

    assert summary.failed == 1

    saved = settings_store.load()

    assert saved.baseline_completed is False
    assert saved.onboarding_completed is False

    assert (
        service.is_ready_for_production()
        is False
    )
