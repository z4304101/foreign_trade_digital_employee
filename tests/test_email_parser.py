from mail_reader.parser import parse_email


def test_parse_plain_text_email():
    raw_email = (
        b"From: Alex <alex@example.com>\r\n"
        b"To: sales@example.com\r\n"
        b"Subject: Inquiry for Model R2\r\n"
        b"Date: Fri, 11 Sep 2026 15:40:28 +0800\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Hello,\r\n"
        b"\r\n"
        b"We are interested in Model R2 and would like to purchase 20 units.\r\n"
        b"\r\n"
        b"Could you please provide the price, delivery time to Moscow, "
        b"and your payment terms?\r\n"
    )

    mail = parse_email(raw_email)

    assert mail.sender == "Alex <alex@example.com>"
    assert mail.subject == "Inquiry for Model R2"
    assert mail.date == "Fri, 11 Sep 2026 15:40:28 +0800"

    assert "Model R2" in mail.body
    assert "20 units" in mail.body
    assert "Moscow" in mail.body