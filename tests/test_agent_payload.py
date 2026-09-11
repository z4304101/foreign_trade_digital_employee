from mail_reader.parser import ParsedEmail
from mail_reader.agent_payload import build_agent_payload


def test_build_agent_payload_preserves_customer_email():
    mail = ParsedEmail(
        sender="Alex <alex@example.com>",
        subject="Inquiry for Model R2",
        date="Fri, 11 Sep 2026 15:40:28 +0800",
        body=(
            "Hello,\n\n"
            "We are interested in Model R2 and would like "
            "to purchase 20 units.\n\n"
            "Could you please provide the price, delivery "
            "time to Moscow, and your payment terms?"
        ),
    )

    payload = build_agent_payload(mail)

    assert "UNTRUSTED_CUSTOMER_EMAIL_BEGIN" in payload
    assert "UNTRUSTED_CUSTOMER_EMAIL_END" in payload

    assert "Alex <alex@example.com>" in payload
    assert "Inquiry for Model R2" in payload
    assert "20 units" in payload
    assert "Moscow" in payload


def test_build_agent_payload_separates_current_message_from_previous_thread():
    mail = ParsedEmail(
        sender='赵鑫 <a4304105@163.com>',
        subject='Re:',
        date='Fri, 11 Sep 2026 16:18:58 +0800',
        body=(
            "Subject: Inquiry for Model R2\n\n"
            "Hello,\n\n"
            "We are interested in Model R2 and would like to purchase 20 units.\n\n"
            "Could you please provide the price, delivery time to Moscow,\n"
            "and your payment terms?\n\n"
            "Thank you.\n\n"
            "Best regards,\n"
            "Alex\n\n"
            '在 2026-09-11 15:40:28，"赵鑫" <a4304107@163.com> 写道：\n\n'
            "| 小五传媒文化有限公司 |\n"
            "| 赵鑫 |\n"
            "外贸数字员工邮件测试"
        ),
    )

    payload = build_agent_payload(mail)

    assert "## Current Message" in payload
    assert "## Previous Thread" in payload

    current_section = payload.split("## Current Message", 1)[1].split(
        "## Previous Thread", 1
    )[0]

    previous_section = payload.split("## Previous Thread", 1)[1]

    assert "Model R2" in current_section
    assert "20 units" in current_section
    assert "Moscow" in current_section

    assert "小五传媒文化有限公司" not in current_section
    assert "小五传媒文化有限公司" in previous_section