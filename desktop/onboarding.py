from collections.abc import Callable

from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    CredentialStore,
)
from desktop.paths import DesktopPaths
from desktop.settings_store import SettingsStore

from history_learning.reply_baseline import (
    seed_processed_store_from_history,
)
from history_learning.service import (
    run_initial_learning,
)
from history_learning.store import (
    HistoryStore,
)
from llm.factory import (
    create_llm_provider,
)


class OnboardingService:
    """
    Desktop first-run configuration coordinator.

    Production processing remains blocked until
    configuration and the safe history baseline
    are both ready.
    """

    def __init__(
        self,
        settings_store: SettingsStore,
        credential_store: CredentialStore,
        paths: DesktopPaths,
        core_bridge_factory: Callable,
    ) -> None:
        self.settings_store = settings_store
        self.credential_store = credential_store
        self.paths = paths
        self.core_bridge_factory = core_bridge_factory

    def is_ready_for_production(
        self,
    ) -> bool:
        settings = self.settings_store.load()

        if not settings.onboarding_completed:
            return False

        if not settings.baseline_completed:
            return False

        if not settings.email_user.strip():
            return False

        if not self.credential_store.get(
            EMAIL_AUTH_CODE
        ):
            return False

        if not self.credential_store.get(
            AI_API_KEY
        ):
            return False

        if not settings.llm_model.strip():
            return False

        if not settings.llm_base_url.strip():
            return False

        if settings.wecom_enabled:
            if not self.credential_store.get(
                WECOM_WEBHOOK
            ):
                return False

        return True

    def run_initial_history_learning(
        self,
    ):
        """
        Run the existing initial history-learning
        workflow and establish the safe reply baseline.

        The production gate is opened only after:

        1. Existing history learning completes.
        2. HistoryStore confirms initial learning completed.
        3. Historical incoming Message-IDs are seeded into
           the processed store.

        Any exception before the final settings save keeps
        production blocked.
        """

        settings = self.settings_store.load()

        bridge = self.core_bridge_factory(
            settings=settings,
            credentials=self.credential_store,
            paths=self.paths,
        )

        mail_config = (
            bridge.build_mail_config()
        )

        llm_config = (
            bridge.build_llm_config()
        )

        provider = create_llm_provider(
            config=llm_config,
        )

        summary = run_initial_learning(
            mail_config=mail_config,
            provider=provider,
            db_path=self.paths.history_db,
        )

        # Any failed historical message keeps the
        # production gate closed, even if the history
        # database reports a completed learning state.
        if summary.failed > 0:
            return summary

        history_store = HistoryStore(
            self.paths.history_db
        )
        history_store.initialize()

        learning_state = (
            history_store.get_learning_state()
        )

        learning_completed = (
            learning_state.get(
                "initial_learning_completed",
                "",
            )
            == "true"
        )

        if not learning_completed:
            return summary

        seed_processed_store_from_history(
            store=history_store,
            processed_store_path=(
                self.paths.processed_store
            ),
        )

        # Open the production gate only after both
        # history learning and processed baseline
        # creation have succeeded.
        settings = self.settings_store.load()

        settings.baseline_completed = True
        settings.onboarding_completed = True

        self.settings_store.save(
            settings
        )

        return summary
