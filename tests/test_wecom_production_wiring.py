from types import SimpleNamespace


def test_run_production_loads_wecom_config_and_runs_batch(
    monkeypatch,
):
    import run_foreign_trade_agent as runner

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
        "load_wecom_config",
        lambda: fake_wecom_config,
        raising=False,
    )

    def fake_batch_main(
        wecom_config=None,
    ):
        calls["wecom_config"] = wecom_config

        return {
            "total": 1,
            "processed": 1,
            "skipped": 0,
            "failed": 0,
        }

    monkeypatch.setattr(
        runner,
        "batch_main",
        fake_batch_main,
    )

    summary = runner.run_production()

    assert summary == {
        "total": 1,
        "processed": 1,
        "skipped": 0,
        "failed": 0,
    }

    assert (
        calls["wecom_config"]
        is fake_wecom_config
    )