from types import SimpleNamespace


def test_run_batch_processes_recent_emails_oldest_to_newest(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    mail_a = SimpleNamespace(
        message_id="<message-a@example.com>",
    )

    mail_b = SimpleNamespace(
        message_id="<message-b@example.com>",
    )

    mail_c = SimpleNamespace(
        message_id="<message-c@example.com>",
    )

    mails = [
        mail_a,
        mail_b,
        mail_c,
    ]

    monkeypatch.setattr(
        runner,
        "read_recent_emails",
        lambda config, limit=20: mails,
        raising=False,
    )

    calls = []

    def fake_process_mail(
        mail,
        provider,
        mail_config,
        skill_path,
        result_path,
        processed_store_path,
        create_draft=True,
    ):
        calls.append(
            mail.message_id
        )

        if (
            mail.message_id
            == "<message-b@example.com>"
        ):
            return runner.SKIPPED_ALREADY_PROCESSED

        return (
            "RESULT:"
            + mail.message_id
        )

    monkeypatch.setattr(
        runner,
        "process_mail",
        fake_process_mail,
        raising=False,
    )

    summary = runner.run_batch(
        provider=object(),
        mail_config=object(),
        skill_path=tmp_path / "SKILL.md",
        result_path=tmp_path / "latest_reply.md",
        processed_store_path=(
            tmp_path / "processed_message_ids.txt"
        ),
        limit=20,
        create_draft=True,
    )

    assert calls == [
        "<message-a@example.com>",
        "<message-b@example.com>",
        "<message-c@example.com>",
    ]

    assert summary == {
        "total": 3,
        "processed": 2,
        "skipped": 1,
        "failed": 0,
    }


def test_run_batch_continues_when_one_email_fails(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    mails = [
        SimpleNamespace(
            message_id="<message-a@example.com>",
        ),
        SimpleNamespace(
            message_id="<message-b@example.com>",
        ),
        SimpleNamespace(
            message_id="<message-c@example.com>",
        ),
    ]

    monkeypatch.setattr(
        runner,
        "read_recent_emails",
        lambda config, limit=20: mails,
        raising=False,
    )

    calls = []

    def fake_process_mail(
        mail,
        provider,
        mail_config,
        skill_path,
        result_path,
        processed_store_path,
        create_draft=True,
    ):
        calls.append(
            mail.message_id
        )

        if (
            mail.message_id
            == "<message-b@example.com>"
        ):
            raise RuntimeError(
                "simulated processing failure"
            )

        return (
            "RESULT:"
            + mail.message_id
        )

    monkeypatch.setattr(
        runner,
        "process_mail",
        fake_process_mail,
        raising=False,
    )

    summary = runner.run_batch(
        provider=object(),
        mail_config=object(),
        skill_path=tmp_path / "SKILL.md",
        result_path=tmp_path / "latest_reply.md",
        processed_store_path=(
            tmp_path / "processed_message_ids.txt"
        ),
        limit=20,
        create_draft=True,
    )

    assert calls == [
        "<message-a@example.com>",
        "<message-b@example.com>",
        "<message-c@example.com>",
    ]

    assert summary == {
        "total": 3,
        "processed": 2,
        "skipped": 0,
        "failed": 1,
    }


def test_run_batch_returns_zero_summary_when_no_email(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    monkeypatch.setattr(
        runner,
        "read_recent_emails",
        lambda config, limit=20: [],
        raising=False,
    )

    summary = runner.run_batch(
        provider=object(),
        mail_config=object(),
        skill_path=tmp_path / "SKILL.md",
        result_path=tmp_path / "latest_reply.md",
        processed_store_path=(
            tmp_path / "processed_message_ids.txt"
        ),
        limit=20,
        create_draft=True,
    )

    assert summary == {
        "total": 0,
        "processed": 0,
        "skipped": 0,
        "failed": 0,
    }
def test_batch_main_wires_configs_provider_and_batch_runner(
    tmp_path,
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

    def fake_create_llm_provider(config):
        assert config is fake_llm_config
        return fake_provider

    monkeypatch.setattr(
        runner,
        "create_llm_provider",
        fake_create_llm_provider,
    )

    def fake_run_batch(
        provider,
        mail_config,
        skill_path,
        result_path,
        processed_store_path,
        limit,
        create_draft,
    ):
        calls["provider"] = provider
        calls["mail_config"] = mail_config
        calls["skill_path"] = skill_path
        calls["result_path"] = result_path
        calls["processed_store_path"] = (
            processed_store_path
        )
        calls["limit"] = limit
        calls["create_draft"] = create_draft

        return {
            "total": 5,
            "processed": 2,
            "skipped": 2,
            "failed": 1,
        }

    monkeypatch.setattr(
        runner,
        "run_batch",
        fake_run_batch,
    )

    summary = runner.batch_main()

    assert summary == {
        "total": 5,
        "processed": 2,
        "skipped": 2,
        "failed": 1,
    }

    assert calls["provider"] is fake_provider
    assert calls["mail_config"] is fake_mail_config

    assert calls["skill_path"] == runner.SKILL_PATH
    assert calls["result_path"] == runner.RESULT_PATH

    assert (
        calls["processed_store_path"]
        == runner.PROCESSED_STORE_PATH
    )

    assert calls["limit"] == 20
    assert calls["create_draft"] is True