from types import SimpleNamespace

import pytest


AGENT_RESULT = """
## Customer Language

French

## Chinese Translation

客户正在询问产品信息。

## Customer Intent

PRODUCT_INQUIRY

## Key Information

Model: R2

## Missing Information

Price

## Internal Verification Required

Pricing requires internal verification.

## Risk Assessment

Risk Level: MEDIUM

## Recommended Action

Verify pricing internally.

## Reply Draft

Dear Pierre,

Thank you for your inquiry. The requested commercial
information is subject to internal verification.

Best regards

## Chinese Back-Translation

Pierre 您好，

感谢您的询问。相关商业信息需要内部确认。

此致

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""


def test_process_mail_uses_history_context_loader(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    mail = SimpleNamespace(
        message_id="<new@example.com>",
        sender="Pierre <pierre@example.com>",
        recipients="sales@example.cn",
        subject="RFQ",
        date="",
        body="Please quote Model R2.",
    )

    mail_config = SimpleNamespace(
        email_user="sales@example.cn",
    )

    captured = {}

    monkeypatch.setattr(
        runner,
        "is_message_processed",
        lambda message_id, store_path: False,
    )

    def fake_build_agent_payload(
        input_mail,
        history_context="",
    ):
        captured["history_context"] = (
            history_context
        )

        return "FINAL PAYLOAD"

    monkeypatch.setattr(
        runner,
        "build_agent_payload",
        fake_build_agent_payload,
    )

    monkeypatch.setattr(
        runner,
        "run_foreign_trade_agent",
        lambda **kwargs: AGENT_RESULT,
    )

    monkeypatch.setattr(
        runner,
        "save_analysis_history",
        lambda **kwargs: (
            tmp_path / "history.md"
        ),
    )

    def fake_history_loader(
        input_mail,
    ):
        assert (
            input_mail.message_id
            == "<new@example.com>"
        )

        return (
            "HISTORICAL_MEMORY_BEGIN\n"
            "SAFE CUSTOMER HISTORY\n"
            "HISTORICAL_MEMORY_END"
        )

    result = runner.process_mail(
        mail=mail,
        provider=object(),
        mail_config=mail_config,
        skill_path=tmp_path / "SKILL.md",
        result_path=tmp_path / "latest.md",
        processed_store_path=(
            tmp_path / "processed.txt"
        ),
        create_draft=False,
        history_context_loader=(
            fake_history_loader
        ),
    )

    assert result == AGENT_RESULT

    assert (
        "SAFE CUSTOMER HISTORY"
        in captured["history_context"]
    )


def test_final_draft_accepts_user_editable_english_signature(
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    mail = SimpleNamespace(
        sender="Pierre <pierre@example.com>",
        reply_to="",
        subject="RFQ",
        message_id="<m1@example.com>",
        references="",
    )

    mail_config = SimpleNamespace(
        sender_name="Hazel He",
        sender_title="Sales Manager",
        sender_company="ABC Robotics Co., Ltd.",
    )

    captured = {}

    def fake_build_reply_message(
        mail,
        sender_email,
        reply_body,
    ):
        captured["reply_body"] = (
            reply_body
        )

        return object()

    monkeypatch.setattr(
        runner,
        "build_reply_message",
        fake_build_reply_message,
    )

    monkeypatch.setattr(
        runner,
        "save_draft",
        lambda **kwargs: "Drafts",
    )

    result = runner.create_reply_draft(
        mail=mail,
        agent_result=AGENT_RESULT,
        mail_config=mail_config,
        sender_email="sales@example.cn",
    )

    assert result == "Drafts"

    assert "Hazel He" in (
        captured["reply_body"]
    )

    assert "Sales Manager" in (
        captured["reply_body"]
    )

    assert (
        "ABC Robotics Co., Ltd."
        in captured["reply_body"]
    )


def test_sender_title_and_company_can_be_left_blank(
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    mail = SimpleNamespace(
        sender="Pierre <pierre@example.com>",
        reply_to="",
        subject="RFQ",
        message_id="<m2@example.com>",
        references="",
    )

    mail_config = SimpleNamespace(
        sender_name="Hazel",
        sender_title="",
        sender_company="",
    )

    captured = {}

    monkeypatch.setattr(
        runner,
        "build_reply_message",
        lambda mail, sender_email, reply_body: (
            captured.setdefault(
                "reply_body",
                reply_body,
            )
            or object()
        ),
    )

    monkeypatch.setattr(
        runner,
        "save_draft",
        lambda **kwargs: "Drafts",
    )

    runner.create_reply_draft(
        mail=mail,
        agent_result=AGENT_RESULT,
        mail_config=mail_config,
        sender_email="sales@example.cn",
    )

    assert "Hazel" in (
        captured["reply_body"]
    )
