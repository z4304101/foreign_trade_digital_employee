import json
import urllib.error
import urllib.request


def build_inquiry_notification(
    mail,
) -> str:
    """
    Build an internal WeCom notification
    for a successfully processed customer email.

    This function only builds text.
    It never sends customer email.
    """

    sender = getattr(
        mail,
        "sender",
        "",
    ) or "(unknown sender)"

    subject = getattr(
        mail,
        "subject",
        "",
    ) or "(no subject)"

    return (
        "📩 New customer inquiry\n\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n\n"
        "✅ AI analysis completed\n"
        "✅ Reply draft saved to mailbox\n"
        "✅ Customer email was not automatically sent"
    )


def send_wecom_text(
    webhook_url: str,
    content: str,
    timeout: int = 10,
) -> bool:
    """
    Send a text message to a WeCom group robot.

    Returns:
        True:
            WeCom accepted the message.

        False:
            Webhook is missing,
            network error,
            invalid response,
            or WeCom returned an error.

    Important:
        WeCom is a secondary notification channel.
        Failure here must not break email processing.
    """

    if not webhook_url or not webhook_url.strip():
        return False

    payload = {
        "msgtype": "text",
        "text": {
            "content": content,
        },
    }

    request_data = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        url=webhook_url,
        data=request_data,
        headers={
            "Content-Type": (
                "application/json; charset=utf-8"
            ),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            response_body = (
                response
                .read()
                .decode("utf-8")
            )

        result = json.loads(
            response_body
        )

        return result.get("errcode") == 0

    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
    ):
        return False