from llm.config import LLMConfig


class FakeMessage:
    content = "FAKE FOREIGN TRADE REPLY"


class FakeChoice:
    message = FakeMessage()


class FakeResponse:
    choices = [FakeChoice()]


class FakeCompletions:
    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return FakeResponse()


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


def test_siliconflow_provider_generates_reply_without_real_network():
    from llm.siliconflow import SiliconFlowProvider

    config = LLMConfig(
        provider="siliconflow",
        api_key="test-key",
        model="deepseek-ai/DeepSeek-V4-Flash",
        base_url="https://api.siliconflow.cn/v1",
    )

    fake_client = FakeClient()

    provider = SiliconFlowProvider(
        config=config,
        client=fake_client,
    )

    result = provider.generate_reply(
        skill_text="SKILL RULES HERE",
        customer_email="CUSTOMER EMAIL HERE",
    )

    assert result == "FAKE FOREIGN TRADE REPLY"

    request = fake_client.chat.completions.last_request

    assert request["model"] == "deepseek-ai/DeepSeek-V4-Flash"

    assert request["messages"][0]["role"] == "system"
    assert "SKILL RULES HERE" in request["messages"][0]["content"]

    assert request["messages"][1]["role"] == "user"
    assert "CUSTOMER EMAIL HERE" in request["messages"][1]["content"]

    assert request["stream"] is False