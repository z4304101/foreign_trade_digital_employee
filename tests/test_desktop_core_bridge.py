from pathlib import Path

import run_foreign_trade_agent as runner

from mail_reader.config import MailConfig


def test_run_configured_production_uses_explicit_paths(
    tmp_path: Path,
    monkeypatch,
):
    captured = {}

    expected_summary = {
        "total": 1,
        "processed": 1,
        "skipped": 0,
        "failed": 0,
    }

    def fake_run_batch(**kwargs):
        captured.update(kwargs)
        return expected_summary

    monkeypatch.setattr(
        runner,
        "run_batch",
        fake_run_batch,
    )

    mail_config = MailConfig(
        email_user="sales@163.com",
        auth_code="mail-secret",
        imap_host="imap.163.com",
        imap_port=993,
        sender_name="Test User",
        sender_title="Sales",
        sender_company="Test Company",
    )

    provider = object()

    skill_path = tmp_path / "SKILL.md"
    result_path = tmp_path / "result" / "latest_reply.md"
    processed_path = (
        tmp_path / "processed_message_ids.txt"
    )
    history_db_path = (
        tmp_path / "history_learning.db"
    )

    summary = runner.run_configured_production(
        mail_config=mail_config,
        provider=provider,
        wecom_config=None,
        skill_path=skill_path,
        result_path=result_path,
        processed_store_path=processed_path,
        history_db_path=history_db_path,
        limit=7,
    )

    assert summary == expected_summary

    assert (
        captured["mail_config"]
        is mail_config
    )

    assert (
        captured["provider"]
        is provider
    )

    assert (
        captured["skill_path"]
        == skill_path
    )

    assert (
        captured["result_path"]
        == result_path
    )

    assert (
        captured["processed_store_path"]
        == processed_path
    )

    assert captured["limit"] == 7
    assert captured["create_draft"] is True

from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    MemoryCredentialStore,
)
from desktop.models import DesktopSettings
from desktop.paths import DesktopPaths


def test_desktop_core_bridge_builds_configs_from_secure_sources(
    tmp_path: Path,
):
    from desktop.core_bridge import DesktopCoreBridge

    settings = DesktopSettings(
        email_user="sales@163.com",
        sender_name="Alice",
        sender_title="Sales Manager",
        sender_company="Example Ltd",
        imap_host="imap.163.com",
        imap_port=993,
        llm_provider="siliconflow",
        llm_model="test-model",
        llm_base_url="https://api.example.invalid/v1",
        wecom_enabled=True,
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

    paths = DesktopPaths.from_root(
        tmp_path
    )

    bridge = DesktopCoreBridge(
        settings=settings,
        credentials=credentials,
        paths=paths,
    )

    mail_config = bridge.build_mail_config()

    assert mail_config.email_user == "sales@163.com"
    assert mail_config.auth_code == "mail-secret"
    assert mail_config.imap_host == "imap.163.com"
    assert mail_config.imap_port == 993
    assert mail_config.sender_name == "Alice"
    assert mail_config.sender_title == "Sales Manager"
    assert mail_config.sender_company == "Example Ltd"

    llm_config = bridge.build_llm_config()

    assert llm_config.provider == "siliconflow"
    assert llm_config.api_key == "ai-secret"
    assert llm_config.model == "test-model"
    assert (
        llm_config.base_url
        == "https://api.example.invalid/v1"
    )

    wecom_config = bridge.build_wecom_config()

    assert (
        wecom_config.webhook_url
        == "https://example.invalid/wecom-hook"
    )
    assert wecom_config.enabled is True


def test_desktop_core_bridge_run_mail_cycle_reuses_production_entry(
    tmp_path: Path,
    monkeypatch,
):
    import desktop.core_bridge as core_bridge_module
    from desktop.core_bridge import DesktopCoreBridge

    settings = DesktopSettings(
        email_user="sales@163.com",
        sender_name="Alice",
        sender_title="Sales",
        sender_company="Example Ltd",
        llm_provider="siliconflow",
        llm_model="test-model",
        llm_base_url="https://api.example.invalid/v1",
        wecom_enabled=True,
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

    paths = DesktopPaths.from_root(
        tmp_path
    )
    paths.ensure()

    fake_provider = object()

    captured = {}

    def fake_create_llm_provider(
        config,
    ):
        captured["llm_config"] = config
        return fake_provider

    expected_summary = {
        "total": 3,
        "processed": 1,
        "skipped": 2,
        "failed": 0,
    }

    def fake_run_configured_production(
        **kwargs,
    ):
        captured.update(kwargs)
        return expected_summary

    monkeypatch.setattr(
        core_bridge_module,
        "create_llm_provider",
        fake_create_llm_provider,
        raising=False,
    )

    monkeypatch.setattr(
        core_bridge_module,
        "run_configured_production",
        fake_run_configured_production,
        raising=False,
    )

    bridge = DesktopCoreBridge(
        settings=settings,
        credentials=credentials,
        paths=paths,
    )

    summary = bridge.run_mail_cycle()

    assert summary == expected_summary

    assert (
        captured["provider"]
        is fake_provider
    )

    assert (
        captured["mail_config"].email_user
        == "sales@163.com"
    )

    assert (
        captured["result_path"]
        == paths.result_dir / "latest_reply.md"
    )

    assert (
        captured["processed_store_path"]
        == paths.processed_store
    )

    assert (
        captured["history_db_path"]
        == paths.history_db
    )

    assert captured["wecom_config"].enabled is True


def test_desktop_core_bridge_verify_mail_reuses_existing_imap_check(
    tmp_path: Path,
    monkeypatch,
):
    import desktop.core_bridge as core_bridge_module
    from desktop.core_bridge import DesktopCoreBridge

    settings = DesktopSettings(
        email_user="sales@163.com",
        imap_host="imap.163.com",
        imap_port=993,
    )

    credentials = MemoryCredentialStore()
    credentials.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )

    paths = DesktopPaths.from_root(
        tmp_path
    )

    captured = {}

    def fake_verify_imap_login(
        config,
    ):
        captured["config"] = config
        return True

    monkeypatch.setattr(
        core_bridge_module,
        "verify_imap_login",
        fake_verify_imap_login,
        raising=False,
    )

    bridge = DesktopCoreBridge(
        settings=settings,
        credentials=credentials,
        paths=paths,
    )

    result = bridge.verify_mail()

    assert result is True

    assert (
        captured["config"].email_user
        == "sales@163.com"
    )

    assert (
        captured["config"].auth_code
        == "mail-secret"
    )

    assert (
        captured["config"].imap_host
        == "imap.163.com"
    )

    assert (
        captured["config"].imap_port
        == 993
    )


def test_desktop_core_bridge_test_wecom_reuses_existing_notifier(
    tmp_path: Path,
    monkeypatch,
):
    import desktop.core_bridge as core_bridge_module
    from desktop.core_bridge import DesktopCoreBridge

    settings = DesktopSettings(
        email_user="sales@163.com",
        wecom_enabled=True,
    )

    credentials = MemoryCredentialStore()
    credentials.set(
        WECOM_WEBHOOK,
        "https://example.invalid/wecom-hook",
    )

    paths = DesktopPaths.from_root(
        tmp_path
    )

    captured = {}

    def fake_send_wecom_text(
        webhook_url,
        content,
        timeout=10,
    ):
        captured["webhook_url"] = webhook_url
        captured["content"] = content
        captured["timeout"] = timeout
        return True

    monkeypatch.setattr(
        core_bridge_module,
        "send_wecom_text",
        fake_send_wecom_text,
        raising=False,
    )

    bridge = DesktopCoreBridge(
        settings=settings,
        credentials=credentials,
        paths=paths,
    )

    result = bridge.test_wecom()

    assert result is True

    assert (
        captured["webhook_url"]
        == "https://example.invalid/wecom-hook"
    )

    assert captured["content"] == (
        "✅ 外贸数字员工已连接\n\n"
        "邮箱连接正常\n"
        "AI 服务正常\n"
        "企业微信通知正常\n\n"
        "数字员工已经可以开始工作。"
    )
