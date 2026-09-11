def test_load_llm_config_for_siliconflow(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "siliconflow")
    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    monkeypatch.setenv("SILICONFLOW_MODEL", "test-model")
    monkeypatch.setenv(
        "SILICONFLOW_BASE_URL",
        "https://example.com/v1",
    )

    from llm.config import load_llm_config

    config = load_llm_config()

    assert config.provider == "siliconflow"
    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.base_url == "https://example.com/v1"