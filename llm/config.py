import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    model: str
    base_url: str


def load_llm_config() -> LLMConfig:
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "").strip().lower()

    if not provider:
        raise ValueError("LLM_PROVIDER is required")

    if provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
        model = os.getenv("SILICONFLOW_MODEL")
        base_url = os.getenv("SILICONFLOW_BASE_URL")

        missing = [
            name
            for name, value in {
                "SILICONFLOW_API_KEY": api_key,
                "SILICONFLOW_MODEL": model,
                "SILICONFLOW_BASE_URL": base_url,
            }.items()
            if not value
        ]

        if missing:
            raise ValueError(
                "Missing required SiliconFlow environment variables: "
                + ", ".join(missing)
            )

        return LLMConfig(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )