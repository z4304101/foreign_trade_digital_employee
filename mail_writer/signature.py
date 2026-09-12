import re


def apply_sender_signature(
    draft: str,
    sender_name: str,
    sender_title: str,
    sender_company: str,
) -> str:
    """
    Apply the configured sender signature
    to an AI-generated reply draft.

    Supported AI output styles:

    1. Placeholder signature:

        [Your Name]
        [Your Title]
        [Your Company]

    2. Generic signature:

        Sales Team

    This function only transforms text.
    It never sends email.
    """

    signature_lines = [
        sender_name,
        sender_title,
        sender_company,
    ]

    signature = "\n".join(
        line
        for line in signature_lines
        if line
    )

    result = draft

    # Replace standard placeholders.
    result = result.replace(
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

    # Some AI replies use a generic sender
    # identity instead of placeholders:
    #
    # Best regards,
    # Sales Team
    #
    # Replace only a complete "Sales Team"
    # line so normal email body content
    # is not accidentally modified.
    if signature:
        result = re.sub(
            r"(?im)^Sales Team\s*$",
            signature,
            result,
        )

    return result