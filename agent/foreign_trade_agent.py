from pathlib import Path

from agent.output_gate import validate_agent_output


def _build_repair_skill_text(
    skill_text: str,
    rejection_reason: str,
) -> str:
    return (
        skill_text
        + "\n\n"
        + "# Automatic Repair Request\n\n"
        + "The previous draft was rejected by the output safety gate.\n\n"
        + f"Gate rejection reason: {rejection_reason}\n\n"
        + "Generate a completely new answer from the original "
        + "customer email.\n\n"
        + "The previous draft was rejected and MUST NOT be reused "
        + "without correction.\n\n"
        + "MUST follow all rules in this SKILL.md.\n\n"
        + "MUST use the exact required section headings.\n\n"
        + "MUST NOT invent or assume commercial facts.\n\n"
        + "MUST NOT promote Previous Thread information into "
        + "current customer facts.\n\n"
        + "MUST NOT include unsupported timing commitments such as "
        + "shortly, soon, promptly, as soon as possible, "
        + "or immediately.\n\n"
        + "The final Send Status MUST remain exactly:\n\n"
        + "WAITING_FOR_HUMAN_APPROVAL\n\n"
        + "Do not mention this repair process in the customer-facing "
        + "reply draft.\n"
    )


def run_foreign_trade_agent(
    provider,
    skill_path,
    customer_email: str,
) -> str:
    skill_text = Path(skill_path).read_text(
        encoding="utf-8",
    )

    first_result = provider.generate_reply(
        skill_text=skill_text,
        customer_email=customer_email,
    )

    try:
        return validate_agent_output(first_result)

    except ValueError as first_error:
        repair_skill_text = _build_repair_skill_text(
            skill_text=skill_text,
            rejection_reason=str(first_error),
        )

        repaired_result = provider.generate_reply(
            skill_text=repair_skill_text,
            customer_email=customer_email,
        )

        return validate_agent_output(repaired_result)