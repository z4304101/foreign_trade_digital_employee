from pathlib import Path

from agent.foreign_trade_agent import run_foreign_trade_agent
from llm.base import LLMProvider
from llm.config import load_llm_config
from llm.factory import create_llm_provider
from mail_reader.agent_payload import build_agent_payload
from mail_reader.config import load_mail_config
from mail_reader.pipeline import read_latest_email


SKILL_PATH = Path(
    "skills/foreign-trade-reply/SKILL.md"
)

RESULT_PATH = Path(
    "result/latest_reply.md"
)


def run_once(
    provider: LLMProvider,
    mail_config,
    skill_path: Path,
    result_path: Path,
) -> str:
    mail = read_latest_email(mail_config)

    customer_email = build_agent_payload(mail)

    result = run_foreign_trade_agent(
        provider=provider,
        skill_path=skill_path,
        customer_email=customer_email,
    )

    result_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_path.write_text(
        result,
        encoding="utf-8",
    )

    return result


def main() -> str:
    mail_config = load_mail_config()
    llm_config = load_llm_config()

    provider = create_llm_provider(
        config=llm_config,
    )

    return run_once(
        provider=provider,
        mail_config=mail_config,
        skill_path=SKILL_PATH,
        result_path=RESULT_PATH,
    )


if __name__ == "__main__":
    result = main()

    print("\n=== Foreign Trade Agent Result ===\n")
    print(result)

    print(
        "\nSaved to:",
        RESULT_PATH.resolve(),
    )