def apply_sender_signature(
    draft: str,
    sender_name: str,
    sender_title: str,
    sender_company: str,
) -> str:
    """
    Replace sender signature placeholders
    in an AI-generated reply draft.

    This function only transforms text.
    It does not send email.
    """

    result = draft.replace(
        "[Your Name]",
        sender_name,
    )

    result = result.replace(
        "[Your Title]",
        sender_title,
    )

    result = result.replace(
        "[Your Company]",
        sender_company,
    )

    return result