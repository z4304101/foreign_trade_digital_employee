def test_wecom_config_is_disabled_when_webhook_missing(
    monkeypatch,
):
    monkeypatch.setenv(
        "WECOM_WEBHOOK_URL",
        "",
    )

    from wecom.config import (
        load_wecom_config,
    )

    config = load_wecom_config()

    assert config.webhook_url == ""
    assert config.enabled is False