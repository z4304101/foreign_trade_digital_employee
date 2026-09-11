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