from types import SimpleNamespace


def test_batch_main_passes_wecom_config_to_batch_runner(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    # This test verifies WeCom wiring only.
    # Do not let a real history DB inject
    # unrelated history_context_loader state.
    monkeypatch.setattr(
        runner,
        "HISTORY_DB_PATH",
        tmp_path / "no-history.db",
    )

    fake_mail_config = object()
    fake_llm_config = object()
    fake_provider = object()

    fake_wecom_config = SimpleNamespace(
        enabled=True,
        webhook_url=(
            "https://qyapi.weixin.qq.com/"
            "cgi-bin/webhook/send?key=fake-key"
        ),
    )

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

    def fake_run_batch(
        provider,
        mail_config,
        skill_path,
        result_path,
        processed_store_path,
        limit,
        create_draft,
        wecom_config=None,
    ):
        calls["provider"] = provider
        calls["mail_config"] = mail_config
        calls["wecom_config"] = wecom_config

        return {
            "total": 1,
            "processed": 1,
            "skipped": 0,
            "failed": 0,
        }

    monkeypatch.setattr(
        runner,
        "run_batch",
        fake_run_batch,
    )

    summary = runner.batch_main(
        wecom_config=fake_wecom_config,
    )

    assert summary == {
        "total": 1,
        "processed": 1,
        "skipped": 0,
        "failed": 0,
    }

    assert calls["provider"] is fake_provider
    assert calls["mail_config"] is fake_mail_config

    assert (
        calls["wecom_config"]
        is fake_wecom_config
    )