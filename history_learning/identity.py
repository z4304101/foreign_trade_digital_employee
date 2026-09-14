from email.utils import getaddresses, parseaddr

from mail_reader.parser import ParsedEmail


def extract_email_address(
    header: str,
) -> str:
    """
    Extract and normalize one email address.

    Examples:
        Pierre <PIERRE@Example.com>
        -> pierre@example.com
    """

    if not header:
        return ""

    _, address = parseaddr(
        header
    )

    address = address.strip().lower()

    if (
        not address
        or "@" not in address
    ):
        return ""

    local_part, domain = address.rsplit(
        "@",
        1,
    )

    if (
        not local_part
        or not domain
    ):
        return ""

    return address


def extract_domain(
    address: str,
) -> str:
    """
    Return the normalized domain
    from an email address.
    """

    normalized = extract_email_address(
        address
    )

    if not normalized:
        return ""

    return normalized.rsplit(
        "@",
        1,
    )[1].lower()


def customer_identity(
    mail: ParsedEmail,
    direction: str,
    own_email: str,
) -> tuple[str, str]:
    """
    Resolve the customer identity for
    incoming or outgoing email.

    Incoming:
        customer = sender

    Outgoing:
        customer = first recipient that
        is not our own mailbox address.
    """

    own_address = extract_email_address(
        own_email
    )

    if direction == "incoming":
        customer_email = (
            extract_email_address(
                mail.sender
            )
        )

        return (
            customer_email,
            extract_domain(
                customer_email
            ),
        )

    if direction == "outgoing":
        addresses = getaddresses(
            [
                mail.recipients
                or ""
            ]
        )

        for _, address in addresses:
            normalized = (
                extract_email_address(
                    address
                )
            )

            if not normalized:
                continue

            if normalized == own_address:
                continue

            return (
                normalized,
                extract_domain(
                    normalized
                ),
            )

        return (
            "",
            "",
        )

    raise ValueError(
        "direction must be "
        "'incoming' or 'outgoing'"
    )
