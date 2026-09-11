from email.utils import parseaddr


NO_REPLY_MARKERS = (
    "noreply",
    "no-reply",
    "do-not-reply",
    "donotreply",
)

SYSTEM_SENDER_MARKERS = (
    "service.netease.com",
    "id.apple.com",
)

SYSTEM_SUBJECT_MARKERS = (
    "新设备登录提醒",
    "登录安全",
    "账号安全",
    "安全提醒",
    "验证码",
    "verification code",
    "verify your apple account",
    "verify your account",
    "verify your email",
    "password reset",
    "login alert",
    "security alert",
    "sign-in alert",
)


def _normalize(
    value: str | None,
) -> str:
    if value is None:
        return ""

    return value.strip().lower()


def _extract_sender_email(
    sender: str | None,
) -> str:
    """
    Extract the actual email address from a sender string.

    Example:

        David Miller <david@example.com>

    becomes:

        david@example.com
    """

    if not sender:
        return ""

    _, address = parseaddr(
        sender
    )

    return _normalize(
        address
    )


def is_customer_email_candidate(
    mail,
) -> bool:
    """
    Decide whether an email should be treated as a
    possible customer/business email.

    This is intentionally conservative:

    - Known system/security/verification emails are ignored.
    - No-reply style senders are ignored.
    - Normal human/business emails remain eligible.
    - We do NOT require subjects to contain RFQ/Inquiry,
      because real customers may use arbitrary subjects such as:
          "Hello"
          "Re: previous discussion"
          "Need more information"
          "Project update"

    Returning True means:
        "This email MAY be a customer email."

    It does NOT mean:
        "This email is definitely a valid quotation request."

    The AI + Output Gate still performs the deeper analysis later.
    """

    sender = _normalize(
        getattr(
            mail,
            "sender",
            "",
        )
    )

    subject = _normalize(
        getattr(
            mail,
            "subject",
            "",
        )
    )

    sender_email = _extract_sender_email(
        sender
    )

    # 1. Reject typical automated/no-reply addresses.
    for marker in NO_REPLY_MARKERS:
        if marker in sender_email:
            return False

    # 2. Reject known system/service sender domains.
    for marker in SYSTEM_SENDER_MARKERS:
        if marker in sender_email:
            return False

    # 3. Reject common security / verification notifications.
    for marker in SYSTEM_SUBJECT_MARKERS:
        if marker in subject:
            return False

    # Default:
    # keep normal human/business mail eligible.
    return True