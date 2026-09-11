import re


def _extract_section(
    output: str,
    section_name: str,
) -> str:
    """
    Extract a Markdown section from the full agent output.

    Example:

        ## Reply Draft

        Dear Customer,

        Thank you...

        ## Chinese Back-Translation

    Only the content under the requested section is returned.
    """

    pattern = (
        rf"^{re.escape(section_name)}[ \t]*\r?\n"
        rf"(.*?)(?=^##[ \t]+|\Z)"
    )

    match = re.search(
        pattern,
        output,
        flags=re.DOTALL | re.MULTILINE,
    )

    if not match:
        return ""

    return match.group(1).strip()


def extract_reply_draft(
    agent_output: str,
) -> str:
    """
    Extract only the customer-facing Reply Draft from
    the complete Foreign Trade Agent result.

    Internal analysis sections are intentionally excluded.
    """

    if not isinstance(agent_output, str):
        raise TypeError(
            "agent_output must be a string"
        )

    if not agent_output.strip():
        raise ValueError(
            "agent_output must not be empty"
        )

    reply_draft = _extract_section(
        agent_output,
        "## Reply Draft",
    )

    if not reply_draft:
        raise ValueError(
            "Reply Draft section is missing or empty"
        )

    return reply_draft