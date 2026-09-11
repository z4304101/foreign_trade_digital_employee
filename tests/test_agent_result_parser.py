def test_extract_reply_draft_from_agent_output():
    from agent.result_parser import extract_reply_draft

    agent_output = """
## Customer Language

English

## Chinese Translation

测试翻译

## Customer Intent

PRICE_INQUIRY

## Key Information

Customer: Michael Brown

## Missing Information

Price

## Internal Verification Required

Price

## Risk Assessment

Risk Level: MEDIUM

## Recommended Action

Verify price internally.

## Reply Draft

Dear Mr. Brown,

Thank you for your inquiry regarding Model R2.

We are currently reviewing the requested commercial details internally.

Best regards,

Sales Team

## Chinese Back-Translation

尊敬的 Brown 先生：

感谢您的询价。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""

    reply = extract_reply_draft(agent_output)

    assert reply == (
        "Dear Mr. Brown,\n\n"
        "Thank you for your inquiry regarding Model R2.\n\n"
        "We are currently reviewing the requested commercial "
        "details internally.\n\n"
        "Best regards,\n\n"
        "Sales Team"
    )


def test_extract_reply_draft_rejects_missing_section():
    import pytest

    from agent.result_parser import extract_reply_draft

    with pytest.raises(
        ValueError,
        match="Reply Draft",
    ):
        extract_reply_draft(
            "## Send Status\n\n"
            "WAITING_FOR_HUMAN_APPROVAL"
        )