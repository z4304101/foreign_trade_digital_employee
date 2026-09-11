from mail_reader.parser import ParsedEmail


def test_normalize_email_separates_current_message_and_previous_thread():
    from mail_reader.normalizer import normalize_email

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
            "Alex\n\n\n"
            '在 2026-09-11 15:40:28，"赵鑫" <a4304107@163.com> 写道：\n\n'
            "| 小五传媒文化有限公司 |\n"
            "| 赵鑫 |\n"
            "外贸数字员工邮件测试"
        ),
    )

    normalized = normalize_email(mail)

    assert "Model R2" in normalized.current_body
    assert "20 units" in normalized.current_body
    assert "Moscow" in normalized.current_body

    assert "在 2026-09-11 15:40:28" not in normalized.current_body
    assert "小五传媒文化有限公司" not in normalized.current_body

    assert "在 2026-09-11 15:40:28" in normalized.previous_thread
    assert "小五传媒文化有限公司" in normalized.previous_thread