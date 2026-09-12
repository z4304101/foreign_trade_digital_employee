from types import SimpleNamespace

from mail_reader.parser import ParsedEmail


def test_create_reply_draft_applies_configured_sender_signature(
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    mail = ParsedEmail(
        sender="Sophia Rossi <sophia@example.com>",
        subject="RFQ for Model R2 - 10 Units",
        date="Sat, 12 Sep 2026 13:20:00 +0800",
        body="Please quote 10 units of Model R2.",
        message_id="<signature-test@example.com>",
    )

    agent_result = """
## Customer Language

English

## Reply Draft

Dear Ms. Rossi,

Thank you for your inquiry regarding Model R2.

Best regards,
[Your Name]
[Your Title]
[Your Company]

## Chinese Back-Translation

感谢您的询价。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""

    mail_config = SimpleNamespace(
        email_user="sales@example.com",
        sender_name="Zhao Xin",
        sender_title="Sales Manager",
        sender_company="EFORT",
    )

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
    )

    mailbox = runner.create_reply_draft(
        mail=mail,
        agent_result=agent_result,
        mail_config=mail_config,
        sender_email=mail_config.email_user,
    )

    assert mailbox == "Drafts"

    body = saved[
        "message"
    ].get_content()

    assert "[Your Name]" not in body
    assert "[Your Title]" not in body
    assert "[Your Company]" not in body

    assert "Zhao Xin" in body
    assert "Sales Manager" in body
    assert "EFORT" in body

    assert (
        "Thank you for your inquiry regarding Model R2."
        in body
    )