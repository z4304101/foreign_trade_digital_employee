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


def _validate_discount_risk(
    output: str,
) -> None:
    normalized_output = output.lower()

    discount_markers = (
        "quantity discount",
        "special discount",
        "discount request",
        "requests a discount",
        "requests a quantity discount",
        "discount available",
        "any discount",
        "数量折扣",
        "特殊折扣",
        "折扣请求",
        "是否有折扣",
        "有无折扣",
    )

    has_discount_request = any(
        marker in normalized_output
        for marker in discount_markers
    )

    if not has_discount_request:
        return

    risk_assessment = _extract_section(
        output,
        "## Risk Assessment",
    )

    normalized_risk = re.sub(
        r"[*`]",
        "",
        risk_assessment,
    )

    high_risk_match = re.search(
        r"risk\s*level\s*:\s*high\b",
        normalized_risk,
        flags=re.IGNORECASE,
    )

    if not high_risk_match:
        raise ValueError(
            "discount request requires Risk Level: HIGH"
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


def _validate_reply_language(
    output: str,
) -> None:
    """
    The customer-facing Reply Draft must be English.

    The Skill prompt is the primary language instruction.
    This gate adds deterministic protection against obvious
    non-English drafts and common accidental language drift.
    """

    reply_draft = _extract_section(
        output,
        "## Reply Draft",
    )

    if not reply_draft:
        raise ValueError(
            "Reply Draft must be written in English"
        )

    # Scripts that clearly indicate the draft is not English.
    non_english_script = re.compile(
        "["
        "\u3400-\u4dbf"   # CJK Extension A
        "\u4e00-\u9fff"   # CJK
        "\u3040-\u309f"   # Hiragana
        "\u30a0-\u30ff"   # Katakana
        "\uac00-\ud7af"   # Hangul
        "\u0400-\u04ff"   # Cyrillic
        "\u0600-\u06ff"   # Arabic
        "\u0590-\u05ff"   # Hebrew
        "\u0e00-\u0e7f"   # Thai
        "\u0900-\u097f"   # Devanagari
        "\u0370-\u03ff"   # Greek
        "]"
    )

    if non_english_script.search(
        reply_draft
    ):
        raise ValueError(
            "Reply Draft must be written in English"
        )

    words = re.findall(
        r"[A-Za-zÀ-ÖØ-öø-ÿ']+",
        reply_draft.lower(),
    )

    # Short English drafts such as "Test reply" remain valid.
    # For normal business replies, require at least one strong
    # English/business-language marker.
    if len(words) >= 4:
        english_markers = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "we",
            "you",
            "your",
            "our",
            "is",
            "are",
            "be",
            "to",
            "of",
            "for",
            "in",
            "on",
            "with",
            "this",
            "that",
            "thank",
            "thanks",
            "dear",
            "regards",
            "please",
            "will",
            "can",
            "could",
            "would",
            "inquiry",
            "information",
            "verification",
            "price",
            "payment",
            "delivery",
            "quotation",
            "quote",
            "order",
            "product",
            "customer",
        }

        if not any(
            word in english_markers
            for word in words
        ):
            raise ValueError(
                "Reply Draft must be written in English"
            )



def _validate_send_status(
    output: str,
) -> None:
    send_status = _extract_section(
        output,
        "## Send Status",
    )

    normalized_status = re.sub(
        r"[*`]",
        "",
        send_status,
    ).strip()

    status_match = re.search(
        r"\bWAITING_FOR_HUMAN_APPROVAL\b",
        normalized_status,
    )

    if not status_match:
        raise ValueError(
            "Send Status must be "
            "WAITING_FOR_HUMAN_APPROVAL"
        )


def validate_agent_output(
    output: str,
) -> str:
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

    _validate_discount_risk(output)

    _validate_timing_commitments(output)

    _validate_reply_language(output)

    _validate_send_status(output)

    return output