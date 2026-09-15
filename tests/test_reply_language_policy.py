from pathlib import Path

import pytest

from agent.output_gate import validate_agent_output


SKILL_PATH = Path(
    "skills/foreign-trade-reply/SKILL.md"
)


def make_output(
    reply_draft: str,
    customer_language: str = "French",
) -> str:
    return f"""
## Customer Language

{customer_language}

## Chinese Translation

客户正在询问产品信息。

## Customer Intent

PRODUCT_INQUIRY

## Key Information

Model: R2

## Missing Information

Price

## Internal Verification Required

Pricing requires internal verification.

## Risk Assessment

Risk Level: MEDIUM

## Recommended Action

Verify the requested commercial information internally.

## Reply Draft

{reply_draft}

## Chinese Back-Translation

感谢您的询问。相关商业信息正在内部确认。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""


def test_skill_requires_reply_draft_to_always_be_english():
    skill = SKILL_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "Reply Draft MUST be written in English"
        in skill
    )

    assert (
        "SHOULD reply in the customer's original language."
        not in skill
    )

    # These two review aids must remain.
    assert (
        "MUST provide a Chinese translation"
        in skill
    )

    assert (
        "MUST provide a Chinese back-translation"
        in skill
    )


def test_output_gate_rejects_obviously_non_english_reply_draft():
    output = make_output(
        reply_draft=(
            "您好，感谢您的询盘。"
            "相关商业信息正在内部确认。"
        ),
        customer_language="Chinese",
    )

    with pytest.raises(
        ValueError,
        match="English",
    ):
        validate_agent_output(
            output
        )


def test_french_customer_can_have_english_reply_and_chinese_review():
    output = make_output(
        reply_draft=(
            "Dear Customer,\n\n"
            "Thank you for your inquiry. "
            "The requested commercial information "
            "is subject to internal verification.\n\n"
            "Best regards"
        ),
        customer_language="French",
    )

    result = validate_agent_output(
        output
    )

    assert (
        "Dear Customer"
        in result
    )

    assert (
        "## Chinese Translation"
        in result
    )

    assert (
        "## Chinese Back-Translation"
        in result
    )
