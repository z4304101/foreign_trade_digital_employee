import pytest


VALID_OUTPUT = """
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

Thank you for your inquiry.

## Chinese Back-Translation

感谢您的咨询。

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""


def test_output_gate_accepts_valid_foreign_trade_result():
    from agent.output_gate import validate_agent_output

    result = validate_agent_output(VALID_OUTPUT)

    assert result == VALID_OUTPUT


def test_output_gate_rejects_missing_human_approval_status():
    from agent.output_gate import validate_agent_output

    invalid_output = VALID_OUTPUT.replace(
        "WAITING_FOR_HUMAN_APPROVAL",
        "SENT",
    )

    with pytest.raises(
        ValueError,
        match="WAITING_FOR_HUMAN_APPROVAL",
    ):
        validate_agent_output(invalid_output)
def test_output_gate_rejects_historical_thread_as_current_fact():
    from agent.output_gate import validate_agent_output

    invalid_output = VALID_OUTPUT.replace(
        "Model: R2",
        (
            "Model: R2\n"
            "Company: 小五传媒文化有限公司"
            "（来自历史邮件，需核实）"
        ),
    )

    with pytest.raises(
        ValueError,
        match="historical",
    ):
        validate_agent_output(invalid_output)
def test_output_gate_rejects_unverified_commercial_assumptions():
    from agent.output_gate import validate_agent_output

    invalid_output = VALID_OUTPUT.replace(
        "Model: R2",
        (
            "Model: R2\n"
            "Currency: Not specified, "
            "but usually defaults to USD"
        ),
    )

    with pytest.raises(
        ValueError,
        match="commercial assumption",
    ):
        validate_agent_output(invalid_output)
def test_output_gate_rejects_unverified_timing_commitment():
    from agent.output_gate import validate_agent_output

    invalid_output = VALID_OUTPUT.replace(
        "Thank you for your inquiry.",
        (
            "Thank you for your inquiry.\n"
            "We will provide the quotation shortly."
        ),
    )

    with pytest.raises(
        ValueError,
        match="timing commitment",
    ):
        validate_agent_output(invalid_output)