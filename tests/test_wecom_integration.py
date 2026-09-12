from types import SimpleNamespace


def test_process_mail_notifies_wecom_after_draft_and_mark(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    fake_mail = SimpleNamespace(
        sender="Emma Wilson <emma@example.com>",
        subject="RFQ for Model R2 - 9 Units",
        date="Fri, 12 Sep 2026 17:30:00 +0800",
        body="Customer inquiry",
        message_id="<wecom-integration@example.com>",
    )

    fake_mail_config = SimpleNamespace(
        email_user="sales@example.com",
    )

    fake_wecom_config = SimpleNamespace(
        enabled=True,
        webhook_url=(
            "https://qyapi.weixin.qq.com/"
            "cgi-bin/webhook/send?key=fake-key"
        ),
    )

    fake_provider = object()

    skill_path = tmp_path / "SKILL.md"
    result_path = tmp_path / "latest_reply.md"
    processed_store_path = (
        tmp_path / "processed_message_ids.txt"
    )

    skill_path.write_text(
        "TEST SKILL",
        encoding="utf-8",
    )

    call_order = []

    monkeypatch.setattr(
        runner,
        "build_agent_payload",
        lambda mail: "CUSTOMER EMAIL PAYLOAD",
    )

    def fake_run_foreign_trade_agent(
        provider,
        skill_path,
        customer_email,
    ):
        call_order.append("agent")

        return "AGENT RESULT"

    monkeypatch.setattr(
        runner,
        "run_foreign_trade_agent",
        fake_run_foreign_trade_agent,
    )

    def fake_create_reply_draft(
        mail,
        agent_result,
        mail_config,
        sender_email,
    ):
        call_order.append("draft")

        return "Drafts"

    monkeypatch.setattr(
        runner,
        "create_reply_draft",
        fake_create_reply_draft,
    )

    def fake_mark_message_processed(
        message_id,
        store_path,
    ):
        call_order.append("mark")

        store_path.write_text(
            message_id + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(
        runner,
        "mark_message_processed",
        fake_mark_message_processed,
    )

    monkeypatch.setattr(
        runner,
        "build_inquiry_notification",
        lambda mail: "TEST WECOM NOTIFICATION",
        raising=False,
    )

    def fake_send_wecom_text(
        webhook_url,
        content,
    ):
        call_order.append("notify")

        assert (
            webhook_url
            == fake_wecom_config.webhook_url
        )

        assert (
            content
            == "TEST WECOM NOTIFICATION"
        )

        return True

    monkeypatch.setattr(
        runner,
        "send_wecom_text",
        fake_send_wecom_text,
        raising=False,
    )

    result = runner.process_mail(
        mail=fake_mail,
        provider=fake_provider,
        mail_config=fake_mail_config,
        skill_path=skill_path,
        result_path=result_path,
        processed_store_path=processed_store_path,
        create_draft=True,
        wecom_config=fake_wecom_config,
    )

    assert result == "AGENT RESULT"

    assert call_order == [
        "agent",
        "draft",
        "mark",
        "notify",
    ]