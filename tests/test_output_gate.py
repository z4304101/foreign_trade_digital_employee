import pytest

from agent.output_gate import validate_agent_output


VALID_OUTPUT = """## Customer Language

English

## Chinese Translation

客户希望采购 20 台 Model R2，并询问价格、交货时间和付款条件。

## Customer Intent

- PRODUCT_INQUIRY
- PRICE_INQUIRY
- DELIVERY_INQUIRY
- PAYMENT_QUESTION

## Key Information

Customer: Alex
Company: Not specified
Product: Model R2
Model: R2
Quantity: 20 units
Destination: Moscow
Requested Date: Not specified
Requested Lead Time: Not specified
Price: Not specified
Currency: Not specified
Incoterm: Not specified
Payment Information: Not specified

## Missing Information

- Verified price
- Verified delivery time
- Verified payment terms
- Applicable Incoterm

## Internal Verification Required

- Model R2 price
- Delivery time to Moscow
- Payment terms
- Incoterm

## Risk Assessment

Risk Level: MEDIUM

Reason: This is a normal commercial inquiry, but pricing, delivery, and payment information still require internal verification.

## Recommended Action

Verify the commercial information internally before replying to the customer.

## Reply Draft

Dear Alex,

Thank you for your inquiry.

We have received your request for 20 units of Model R2 for delivery to Moscow.

The requested pricing, delivery time, payment terms, and Incoterm are currently subject to internal verification.

Best regards,

[Your Name]

## Chinese Back-Translation

尊敬的 Alex：

感谢您的询价。

我们已收到您关于采购 20 台 Model R2 并运往莫斯科的需求。

您所询问的价格、交货时间、付款条件和贸易术语目前正在内部核实。

此致

[您的姓名]

## Send Status

WAITING_FOR_HUMAN_APPROVAL
"""


def test_output_gate_accepts_valid_foreign_trade_result():
    result = validate_agent_output(
        VALID_OUTPUT,
    )

    assert result == VALID_OUTPUT


def test_output_gate_rejects_missing_human_approval_status():
    invalid_output = VALID_OUTPUT.replace(
        "WAITING_FOR_HUMAN_APPROVAL",
        "SENT",
    )

    assert "SENT" in invalid_output
    assert "WAITING_FOR_HUMAN_APPROVAL" not in invalid_output

    with pytest.raises(
        ValueError,
        match="WAITING_FOR_HUMAN_APPROVAL",
    ):
        validate_agent_output(
            invalid_output,
        )


def test_output_gate_rejects_historical_thread_as_current_fact():
    invalid_output = VALID_OUTPUT.replace(
        "Model: R2",
        (
            "Model: R2\n"
            "Company: 小五传媒文化有限公司"
            "（来自历史邮件，需核实）"
        ),
    )

    assert "来自历史邮件" in invalid_output

    with pytest.raises(
        ValueError,
        match="historical",
    ):
        validate_agent_output(
            invalid_output,
        )


def test_output_gate_rejects_unverified_commercial_assumptions():
    invalid_output = VALID_OUTPUT.replace(
        "Currency: Not specified",
        (
            "Currency: Not specified, "
            "but usually defaults to USD"
        ),
    )

    assert "usually defaults to USD" in invalid_output

    with pytest.raises(
        ValueError,
        match="commercial assumption",
    ):
        validate_agent_output(
            invalid_output,
        )


def test_output_gate_rejects_unverified_timing_commitment():
    invalid_output = VALID_OUTPUT.replace(
        "Thank you for your inquiry.",
        (
            "Thank you for your inquiry.\n"
            "We will provide the quotation shortly."
        ),
    )

    assert "shortly" in invalid_output

    with pytest.raises(
        ValueError,
        match="timing commitment",
    ):
        validate_agent_output(
            invalid_output,
        )


def test_output_gate_rejects_discount_request_marked_as_medium():
    invalid_output = VALID_OUTPUT.replace(
        "## Missing Information",
        (
            "Other: Customer requests a quantity "
            "discount for 20 units\n\n"
            "## Missing Information"
        ),
    )

    assert "quantity discount" in invalid_output
    assert "Risk Level: MEDIUM" in invalid_output

    with pytest.raises(
        ValueError,
        match="discount",
    ):
        validate_agent_output(
            invalid_output,
        )