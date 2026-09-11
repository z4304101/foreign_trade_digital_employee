import pytest


def test_llm_provider_requires_generate_reply():
    from llm.base import LLMProvider

    class BrokenProvider(LLMProvider):
        pass

    with pytest.raises(TypeError):
        BrokenProvider()