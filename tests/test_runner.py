from pathlib import Path

from mail_reader.parser import ParsedEmail


VALID_RESULT = """
## Customer Language

English

## Chinese Translation

您好。

## Customer Intent

PRICE_INQUIRY

## Key Information

Model: R2

## Missing Information

Price

## Internal Verification Required

Price verification required.

## Risk Assessment

Risk Level: MEDIUM

## Recommended Action

Verify pricing internally.

## Reply Draft

Test reply

## Chinese Back-Translation

测试回复。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""


class FakeProvider:
    def generate_reply(
        self,
        skill_text: str,
        customer_email: str,
    ) -> str:
        assert "FOREIGN TRADE SKILL RULES" in skill_text
        assert "CURRENT CUSTOMER EMAIL" in customer_email

        return VALID_RESULT


def test_runner_processes_mail_and_writes_result(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    fake_mail = ParsedEmail(
        sender="Alex <alex@example.com>",
        subject="Inquiry for Model R2",
        date="Fri, 11 Sep 2026 15:40:28 +0800",
        body="Customer body",
    )

    monkeypatch.setattr(
        runner,
        "read_latest_email",
        lambda config: fake_mail,
    )

    monkeypatch.setattr(
        runner,
        "build_agent_payload",
        lambda mail: "CURRENT CUSTOMER EMAIL",
    )

    skill_path = tmp_path / "SKILL.md"

    skill_path.write_text(
        "FOREIGN TRADE SKILL RULES",
        encoding="utf-8",
    )

    result_path = tmp_path / "latest_reply.md"

    result = runner.run_once(
        provider=FakeProvider(),
        mail_config=object(),
        skill_path=skill_path,
        result_path=result_path,
    )

    assert result_path.exists()

    saved = result_path.read_text(
        encoding="utf-8",
    )

    assert saved == VALID_RESULT
    assert result == VALID_RESULT


def test_main_wires_configs_provider_and_runner(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    fake_mail_config = object()
    fake_llm_config = object()
    fake_provider = object()

    skill_path = tmp_path / "SKILL.md"
    result_path = tmp_path / "latest_reply.md"

    calls = {}

    monkeypatch.setattr(
        runner,
        "load_mail_config",
        lambda: fake_mail_config,
        raising=False,
    )

    monkeypatch.setattr(
        runner,
        "load_llm_config",
        lambda: fake_llm_config,
        raising=False,
    )

    monkeypatch.setattr(
        runner,
        "create_llm_provider",
        lambda config: fake_provider,
        raising=False,
    )

    monkeypatch.setattr(
        runner,
        "SKILL_PATH",
        skill_path,
        raising=False,
    )

    monkeypatch.setattr(
        runner,
        "RESULT_PATH",
        result_path,
        raising=False,
    )

    def fake_run_once(
        provider,
        mail_config,
        skill_path,
        result_path,
        create_draft=False,
    ):
        calls["provider"] = provider
        calls["mail_config"] = mail_config
        calls["skill_path"] = skill_path
        calls["result_path"] = result_path
        calls["create_draft"] = create_draft

        return "DONE"

    monkeypatch.setattr(
        runner,
        "run_once",
        fake_run_once,
    )

    result = runner.main()

    assert result == "DONE"
    assert calls["provider"] is fake_provider
    assert calls["mail_config"] is fake_mail_config
    assert calls["skill_path"] == skill_path
    assert calls["result_path"] == result_path
    assert calls["create_draft"] is True


def test_create_reply_draft_from_agent_result(
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    from mail_reader.parser import ParsedEmail

    parsed_mail = ParsedEmail(
        sender="Michael Brown <michael@customer.com>",
        subject="Request for Quotation - Model R2",
        date="Fri, 11 Sep 2026 18:30:00 +0800",
        body=(
            "Dear Sales Team,\n\n"
            "Please quote 12 units of Model R2.\n"
        ),
        reply_to="procurement@customer.com",
        message_id="<customer-message-001@example.com>",
        references="<previous-message-001@example.com>",
    )

    agent_result = """
## Customer Language

English

## Chinese Translation

测试翻译

## Customer Intent

QUOTATION_REQUEST

## Key Information

Customer: Michael Brown

## Missing Information

Price

## Internal Verification Required

Price

## Risk Assessment

Risk Level: MEDIUM

## Recommended Action

Verify commercial details internally.

## Reply Draft

Dear Mr. Brown,

Thank you for your inquiry regarding Model R2.

We are currently reviewing the requested commercial details internally.

Best regards,

Sales Team

## Chinese Back-Translation

尊敬的 Brown 先生：

感谢您的询价。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""

    saved = {}

    def fake_save_draft(
        config,
        message,
    ):
        saved["config"] = config
        saved["message"] = message

        return "Drafts"

    monkeypatch.setattr(
        runner,
        "save_draft",
        fake_save_draft,
        raising=False,
    )

    fake_mail_config = object()

    mailbox = runner.create_reply_draft(
        mail=parsed_mail,
        agent_result=agent_result,
        mail_config=fake_mail_config,
        sender_email="sales@example.com",
    )

    assert mailbox == "Drafts"

    message = saved["message"]

    assert saved["config"] is fake_mail_config

    assert message["From"] == "sales@example.com"

    assert (
        message["To"]
        == "procurement@customer.com"
    )

    assert (
        message["Subject"]
        == "Re: Request for Quotation - Model R2"
    )

    assert (
        message["In-Reply-To"]
        == "<customer-message-001@example.com>"
    )

    assert (
        message["References"]
        == (
            "<previous-message-001@example.com> "
            "<customer-message-001@example.com>"
        )
    )

    body = message.get_content()

    assert "Dear Mr. Brown" in body
    assert "Thank you for your inquiry" in body

    assert "Risk Assessment" not in body
    assert "Internal Verification Required" not in body
    assert "Chinese Back-Translation" not in body
    assert "WAITING_FOR_HUMAN_APPROVAL" not in body


def test_run_once_creates_reply_draft_when_enabled(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    from types import SimpleNamespace

    fake_mail = object()

    fake_mail_config = SimpleNamespace(
        email_user="sales@example.com",
    )

    fake_provider = object()

    skill_path = tmp_path / "SKILL.md"
    result_path = tmp_path / "latest_reply.md"

    skill_path.write_text(
        "TEST SKILL",
        encoding="utf-8",
    )

    agent_result = """
## Customer Language

English

## Chinese Translation

测试翻译

## Customer Intent

QUOTATION_REQUEST

## Key Information

Customer: Michael Brown

## Missing Information

Price

## Internal Verification Required

Price

## Risk Assessment

Risk Level: MEDIUM

## Recommended Action

Verify internally.

## Reply Draft

Dear Mr. Brown,

Thank you for your inquiry.

Best regards,

Sales Team

## Chinese Back-Translation

感谢您的询价。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""

    calls = {}

    def fake_read_latest_email(config):
        calls["read_config"] = config
        return fake_mail

    def fake_build_agent_payload(mail):
        calls["payload_mail"] = mail
        return "CUSTOMER EMAIL PAYLOAD"

    def fake_run_foreign_trade_agent(
        provider,
        skill_path,
        customer_email,
    ):
        calls["provider"] = provider
        calls["skill_path"] = skill_path
        calls["customer_email"] = customer_email

        return agent_result

    def fake_create_reply_draft(
        mail,
        agent_result,
        mail_config,
        sender_email,
    ):
        calls["draft_mail"] = mail
        calls["draft_result"] = agent_result
        calls["draft_config"] = mail_config
        calls["sender_email"] = sender_email

        return "Drafts"

    monkeypatch.setattr(
        runner,
        "read_latest_email",
        fake_read_latest_email,
    )

    monkeypatch.setattr(
        runner,
        "build_agent_payload",
        fake_build_agent_payload,
    )

    monkeypatch.setattr(
        runner,
        "run_foreign_trade_agent",
        fake_run_foreign_trade_agent,
    )

    monkeypatch.setattr(
        runner,
        "create_reply_draft",
        fake_create_reply_draft,
    )

    result = runner.run_once(
        provider=fake_provider,
        mail_config=fake_mail_config,
        skill_path=skill_path,
        result_path=result_path,
        create_draft=True,
    )

    assert result == agent_result

    assert result_path.read_text(
        encoding="utf-8",
    ) == agent_result

    assert calls["draft_mail"] is fake_mail
    assert calls["draft_result"] == agent_result
    assert calls["draft_config"] is fake_mail_config

    assert (
        calls["sender_email"]
        == "sales@example.com"
    )


def test_main_enables_reply_draft_creation(
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    fake_mail_config = object()
    fake_llm_config = object()
    fake_provider = object()

    calls = {}

    monkeypatch.setattr(
        runner,
        "load_mail_config",
        lambda: fake_mail_config,
    )

    monkeypatch.setattr(
        runner,
        "load_llm_config",
        lambda: fake_llm_config,
    )

    monkeypatch.setattr(
        runner,
        "create_llm_provider",
        lambda config: fake_provider,
    )

    def fake_run_once(
        provider,
        mail_config,
        skill_path,
        result_path,
        create_draft=False,
    ):
        calls["provider"] = provider
        calls["mail_config"] = mail_config
        calls["skill_path"] = skill_path
        calls["result_path"] = result_path
        calls["create_draft"] = create_draft

        return "RESULT"

    monkeypatch.setattr(
        runner,
        "run_once",
        fake_run_once,
    )

    result = runner.main()

    assert result == "RESULT"

    assert calls["provider"] is fake_provider
    assert calls["mail_config"] is fake_mail_config

    assert calls["create_draft"] is True