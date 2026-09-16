from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    CredentialStore,
)
from desktop.models import DesktopSettings
from desktop.paths import DesktopPaths

from llm.config import LLMConfig
from llm.factory import create_llm_provider

from mail_reader.config import MailConfig
from mail_reader.imap_client import (
    verify_imap_login,
)

from run_foreign_trade_agent import (
    SKILL_PATH,
    run_configured_production,
)

from wecom.config import WeComConfig
from wecom.notifier import (
    send_wecom_text,
)


WECOM_TEST_MESSAGE = (
    "✅ 外贸数字员工已连接\n\n"
    "邮箱连接正常\n"
    "AI 服务正常\n"
    "企业微信通知正常\n\n"
    "数字员工已经可以开始工作。"
)


class DesktopCoreBridge:
    """
    Bridge between the desktop application and the
    existing foreign-trade business core.

    Responsibilities:

    - Build existing core config objects from desktop settings.
    - Read secrets only from CredentialStore.
    - Reuse the existing production mail workflow.
    - Reuse existing mailbox verification logic.
    - Reuse existing WeCom notification logic.
    - Keep desktop UI code away from mail-processing details.

    This class NEVER sends customer email directly.
    """

    def __init__(
        self,
        settings: DesktopSettings,
        credentials: CredentialStore,
        paths: DesktopPaths,
    ) -> None:
        self.settings = settings
        self.credentials = credentials
        self.paths = paths

    def build_mail_config(
        self,
    ) -> MailConfig:
        auth_code = (
            self.credentials.get(
                EMAIL_AUTH_CODE
            )
            or ""
        )

        return MailConfig(
            email_user=self.settings.email_user,
            auth_code=auth_code,
            imap_host=self.settings.imap_host,
            imap_port=self.settings.imap_port,
            sender_name=self.settings.sender_name,
            sender_title=self.settings.sender_title,
            sender_company=self.settings.sender_company,
        )

    def build_llm_config(
        self,
    ) -> LLMConfig:
        api_key = (
            self.credentials.get(
                AI_API_KEY
            )
            or ""
        )

        return LLMConfig(
            provider=self.settings.llm_provider,
            api_key=api_key,
            model=self.settings.llm_model,
            base_url=self.settings.llm_base_url,
        )

    def build_wecom_config(
        self,
    ) -> WeComConfig:
        webhook_url = (
            self.credentials.get(
                WECOM_WEBHOOK
            )
            or ""
        )

        return WeComConfig(
            webhook_url=webhook_url,
            enabled=(
                self.settings.wecom_enabled
                and bool(webhook_url)
            ),
        )

    def verify_mail(
        self,
    ) -> bool:
        """
        Verify the configured mailbox by reusing the
        existing IMAP login + ID verification logic.
        """

        return verify_imap_login(
            self.build_mail_config()
        )

    def test_wecom(
        self,
    ) -> bool:
        """
        Send the fixed Desktop V1 WeCom connection
        test message through the existing notifier.
        """

        config = self.build_wecom_config()

        if not config.enabled:
            return False

        return send_wecom_text(
            webhook_url=config.webhook_url,
            content=WECOM_TEST_MESSAGE,
        )

    def run_mail_cycle(
        self,
    ) -> dict[str, int]:
        """
        Run one production mail-processing cycle.

        This method deliberately delegates to the same
        production entry point used by the existing CLI.

        No duplicate desktop-specific mail-processing
        pipeline is implemented here.
        """

        self.paths.ensure()

        mail_config = (
            self.build_mail_config()
        )

        llm_config = (
            self.build_llm_config()
        )

        wecom_config = (
            self.build_wecom_config()
        )

        provider = create_llm_provider(
            config=llm_config,
        )

        return run_configured_production(
            mail_config=mail_config,
            provider=provider,
            wecom_config=wecom_config,
            skill_path=SKILL_PATH,
            result_path=(
                self.paths.result_dir
                / "latest_reply.md"
            ),
            processed_store_path=(
                self.paths.processed_store
            ),
            history_db_path=(
                self.paths.history_db
            ),
        )
