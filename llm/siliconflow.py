from openai import OpenAI

from llm.base import LLMProvider
from llm.config import LLMConfig


class SiliconFlowProvider(LLMProvider):
    def __init__(
        self,
        config: LLMConfig,
        client=None,
    ):
        if config.provider != "siliconflow":
            raise ValueError(
                "SiliconFlowProvider requires "
                "provider='siliconflow'"
            )

        self.config = config

        if client is not None:
            self.client = client
        else:
            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
            )

    def generate_reply(
        self,
        skill_text: str,
        customer_email: str,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": skill_text,
                },
                {
                    "role": "user",
                    "content": customer_email,
                },
            ],
            stream=False,
        )

        if not response.choices:
            raise RuntimeError(
                "SiliconFlow returned no choices"
            )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "SiliconFlow returned empty content"
            )

        return content.strip()