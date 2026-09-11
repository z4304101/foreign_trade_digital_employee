import re


REQUIRED_SECTIONS = (
    "## Customer Language",
    "## Chinese Translation",
    "## Customer Intent",
    "## Key Information",
    "## Missing Information",
    "## Internal Verification Required",
    "## Risk Assessment",
    "## Recommended Action",
    "## Reply Draft",
    "## Chinese Back-Translation",
    "## Send Status",
)


def _extract_section(
    output: str,
    section_name: str,
) -> str:
    pattern = (
        rf"{re.escape(section_name)}\s*\n"
        rf"(.*?)(?=\n## |\Z)"
    )

    match = re.search(
        pattern,
        output,
        flags=re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).strip()


def _validate_historical_context(
    output: str,
) -> None:
    key_information = _extract_section(
        output,
        "## Key Information",
    )

    historical_markers = (
        "来自历史邮件",
        "来自历史线程",
        "来自previous thread",
        "from previous thread",
        "from historical",
        "historical email",
        "historical thread",
    )

    normalized = key_information.lower()

    for marker in historical_markers:
        if marker.lower() in normalized:
            raise ValueError(
                "historical context must not be promoted "
                "to current customer facts"
            )


def _validate_commercial_assumptions(
    output: str,
) -> None:
    key_information = _extract_section(
        output,
        "## Key Information",
    )

    protected_fields = (
        "price",
        "currency",
        "incoterm",
        "payment",
        "lead time",
        "delivery time",
        "价格",
        "币种",
        "货币",
        "付款",
        "交期",
        "交货时间",
    )

    assumption_markers = (
        "default",
        "defaults",
        "usually",
        "normally",
        "typically",
        "assume",
        "assumed",
        "generally",
        "默认",
        "通常",
        "一般",
        "假设",
        "推定",
    )

    for line in key_information.splitlines():
        normalized = line.strip().lower()

        contains_protected_field = any(
            field.lower() in normalized
            for field in protected_fields
        )

        contains_assumption = any(
            marker.lower() in normalized
            for marker in assumption_markers
        )

        if contains_protected_field and contains_assumption:
            raise ValueError(
                "commercial assumption is not allowed "
                "for unverified pricing, currency, payment, "
                "lead time, delivery time, or Incoterm"
            )


def _validate_timing_commitments(
    output: str,
) -> None:
    reply_draft = _extract_section(
        output,
        "## Reply Draft",
    )

    normalized = reply_draft.lower()

    timing_markers = (
        "shortly",
        "very soon",
        "soon",
        "promptly",
        "as soon as possible",
        "immediately",
    )

    for marker in timing_markers:
        if marker in normalized:
            raise ValueError(
                "timing commitment is not allowed "
                "without verified delivery or response timing"
            )


def validate_agent_output(output: str) -> str:
    if not isinstance(output, str) or not output.strip():
        raise ValueError(
            "Agent output must be a non-empty string"
        )

    for section in REQUIRED_SECTIONS:
        if section not in output:
            raise ValueError(
                f"Missing required section: {section}"
            )

    _validate_historical_context(output)
    _validate_commercial_assumptions(output)
    _validate_timing_commitments(output)

    status_match = re.search(
        r"## Send Status\s*\n+\s*([A-Z_]+)",
        output,
    )

    if not status_match:
        raise ValueError(
            "Send Status must be "
            "WAITING_FOR_HUMAN_APPROVAL"
        )

    status = status_match.group(1).strip()

    if status != "WAITING_FOR_HUMAN_APPROVAL":
        raise ValueError(
            "Send Status must be "
            "WAITING_FOR_HUMAN_APPROVAL"
        )

    return output