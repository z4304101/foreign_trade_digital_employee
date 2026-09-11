from llm.base import LLMProvider
from llm.config import LLMConfig


def create_llm_provider(
    config: LLMConfig,
    client=None,
) -> LLMProvider:

    if config.provider == "siliconflow":
        from llm.siliconflow import SiliconFlowProvider

        return SiliconFlowProvider(
            config=config,
            client=client,
        )

    raise ValueError(
        f"Unsupported LLM provider: {config.provider}"
    )