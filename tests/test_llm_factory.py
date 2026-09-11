from llm.config import LLMConfig


def test_factory_creates_siliconflow_provider():
    from llm.factory import create_llm_provider
    from llm.siliconflow import SiliconFlowProvider

    config = LLMConfig(
        provider="siliconflow",
        api_key="test-key",
        model="deepseek-ai/DeepSeek-V4-Flash",
        base_url="https://api.siliconflow.cn/v1",
    )

    fake_client = object()

    provider = create_llm_provider(
        config=config,
        client=fake_client,
    )

    assert isinstance(
        provider,
        SiliconFlowProvider,
    )

    assert provider.client is fake_client