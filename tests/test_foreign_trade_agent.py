import pytest


VALID_RESULT = """
## Customer Language

English

## Chinese Translation

您好。

## Customer Intent

PRICE_INQUIRY

## Key Information

Model: R2

## Missing Information

Price

## Internal Verification Required

Price verification required.

## Risk Assessment

Risk Level: MEDIUM

## Recommended Action

Verify pricing internally.

## Reply Draft

Test reply

## Chinese Back-Translation

测试回复。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""


class FakeProvider:
    def __init__(self):
        self.skill_text = None
        self.customer_email = None

    def generate_reply(
        self,
        skill_text: str,
        customer_email: str,
    ) -> str:
        self.skill_text = skill_text
        self.customer_email = customer_email

        return VALID_RESULT


class UnsafeProvider:
    def generate_reply(
        self,
        skill_text: str,
        customer_email: str,
    ) -> str:
        return VALID_RESULT.replace(
            "WAITING_FOR_HUMAN_APPROVAL",
            "SENT",
        )


def test_foreign_trade_agent_loads_skill_and_calls_provider(tmp_path):
    from agent.foreign_trade_agent import run_foreign_trade_agent

    skill_path = tmp_path / "SKILL.md"

    skill_path.write_text(
        "FOREIGN TRADE SKILL RULES",
        encoding="utf-8",
    )

    provider = FakeProvider()

    result = run_foreign_trade_agent(
        provider=provider,
        skill_path=skill_path,
        customer_email="REAL CUSTOMER EMAIL",
    )

    assert provider.skill_text == "FOREIGN TRADE SKILL RULES"
    assert provider.customer_email == "REAL CUSTOMER EMAIL"

    assert "Test reply" in result
    assert "WAITING_FOR_HUMAN_APPROVAL" in result


def test_foreign_trade_agent_rejects_unsafe_model_output(tmp_path):
    from agent.foreign_trade_agent import run_foreign_trade_agent

    skill_path = tmp_path / "SKILL.md"

    skill_path.write_text(
        "FOREIGN TRADE SKILL RULES",
        encoding="utf-8",
    )

    provider = UnsafeProvider()

    with pytest.raises(
        ValueError,
        match="WAITING_FOR_HUMAN_APPROVAL",
    ):
        run_foreign_trade_agent(
            provider=provider,
            skill_path=skill_path,
            customer_email="REAL CUSTOMER EMAIL",
        )
def test_foreign_trade_agent_retries_once_after_gate_rejection(tmp_path):
    from agent.foreign_trade_agent import run_foreign_trade_agent

    class RepairingProvider:
        def __init__(self):
            self.call_count = 0
            self.skill_texts = []

        def generate_reply(
            self,
            skill_text: str,
            customer_email: str,
        ) -> str:
            self.call_count += 1
            self.skill_texts.append(skill_text)

            if self.call_count == 1:
                return VALID_RESULT.replace(
                    "Test reply",
                    (
                        "Test reply\n"
                        "We will provide the quotation shortly."
                    ),
                )

            return VALID_RESULT

    skill_path = tmp_path / "SKILL.md"

    skill_path.write_text(
        "FOREIGN TRADE SKILL RULES",
        encoding="utf-8",
    )

    provider = RepairingProvider()

    result = run_foreign_trade_agent(
        provider=provider,
        skill_path=skill_path,
        customer_email="REAL CUSTOMER EMAIL",
    )

    assert provider.call_count == 2

    assert "WAITING_FOR_HUMAN_APPROVAL" in result

    assert "shortly" not in result.lower()

    assert len(provider.skill_texts) == 2

    assert "FOREIGN TRADE SKILL RULES" in provider.skill_texts[0]

    assert (
        "previous draft was rejected"
        in provider.skill_texts[1].lower()
    )