from mail_reader.parser import ParsedEmail


def test_reply_recipient_prefers_reply_to():
    from mail_writer.reply_builder import get_reply_recipient

    mail = ParsedEmail(
        sender="Michael Brown <michael@customer.com>",
        subject="Request for Quotation",
        date="Fri, 11 Sep 2026 18:30:00 +0800",
        body="Please send us a quotation.",
        reply_to="procurement@customer.com",
        message_id="<message-001@customer.com>",
        references="",
    )

    recipient = get_reply_recipient(mail)

    assert recipient == "procurement@customer.com"


def test_reply_recipient_falls_back_to_sender():
    from mail_writer.reply_builder import get_reply_recipient

    mail = ParsedEmail(
        sender="Michael Brown <michael@customer.com>",
        subject="Request for Quotation",
        date="Fri, 11 Sep 2026 18:30:00 +0800",
        body="Please send us a quotation.",
        reply_to="",
        message_id="<message-002@customer.com>",
        references="",
    )

    recipient = get_reply_recipient(mail)

    assert recipient == "michael@customer.com"


def test_build_reply_message_preserves_email_thread():
    from mail_writer.reply_builder import build_reply_message

    mail = ParsedEmail(
        sender="Michael Brown <michael@customer.com>",
        subject="Request for Quotation - Model R2",
        date="Fri, 11 Sep 2026 18:30:00 +0800",
        body="Please send us a quotation.",
        reply_to="procurement@customer.com",
        message_id="<message-003@customer.com>",
        references="<message-001@customer.com> <message-002@customer.com>",
    )

    message = build_reply_message(
        mail=mail,
        sender_email="a4304107@163.com",
        reply_body=(
            "Dear Mr. Brown,\n\n"
            "Thank you for your inquiry.\n\n"
            "Best regards,\n"
            "Sales Team"
        ),
    )

    assert message["From"] == "a4304107@163.com"
    assert message["To"] == "procurement@customer.com"

    assert (
        message["Subject"]
        == "Re: Request for Quotation - Model R2"
    )

    assert (
        message["In-Reply-To"]
        == "<message-003@customer.com>"
    )

    assert (
        message["References"]
        == (
            "<message-001@customer.com> "
            "<message-002@customer.com> "
            "<message-003@customer.com>"
        )
    )

    assert "Dear Mr. Brown" in message.get_content()
    assert "Thank you for your inquiry." in message.get_content()