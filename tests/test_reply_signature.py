def test_apply_sender_signature_replaces_placeholders():
    from mail_writer.signature import (
        apply_sender_signature,
    )

    draft = """Dear Ms. Rossi,

Thank you for your inquiry.

Best regards,
[Your Name]
[Your Title]
[Your Company]
"""

    result = apply_sender_signature(
        draft=draft,
        sender_name="Zhao Xin",
        sender_title="Sales Manager",
        sender_company="EFORT",
    )

    assert "[Your Name]" not in result
    assert "[Your Title]" not in result
    assert "[Your Company]" not in result

    assert "Zhao Xin" in result
    assert "Sales Manager" in result
    assert "EFORT" in result


def test_apply_sender_signature_preserves_body_content():
    from mail_writer.signature import (
        apply_sender_signature,
    )

    draft = """Dear Customer,

Thank you for your inquiry regarding Model R2.

Best regards,
[Your Name]
[Your Title]
[Your Company]
"""

    result = apply_sender_signature(
        draft=draft,
        sender_name="Zhao Xin",
        sender_title="Sales Manager",
        sender_company="EFORT",
    )

    assert (
        "Thank you for your inquiry regarding Model R2."
        in result
    )


def test_apply_sender_signature_replaces_generic_sales_team():
    from mail_writer.signature import (
        apply_sender_signature,
    )

    draft = """Dear Mr. Garcia,

Thank you for your inquiry regarding Model R2.

Best regards,
Sales Team
"""

    result = apply_sender_signature(
        draft=draft,
        sender_name="Zhao Xin",
        sender_title="营销总监",
        sender_company="启智（芜湖）智能机器人有限公司",
    )

    assert "Sales Team" not in result

    assert "Zhao Xin" in result
    assert "营销总监" in result
    assert (
        "启智（芜湖）智能机器人有限公司"
        in result
    )

    assert result.rstrip().endswith(
        "Best regards,\n"
        "Zhao Xin\n"
        "营销总监\n"
        "启智（芜湖）智能机器人有限公司"
    )


def test_apply_sender_signature_completes_partial_sender_signature():
    from mail_writer.signature import (
        apply_sender_signature,
    )

    draft = """Dear Mr. Silva,

Thank you for your inquiry regarding Model R2.

Best regards,
Zhao Xin
"""

    result = apply_sender_signature(
        draft=draft,
        sender_name="Zhao Xin",
        sender_title="营销总监",
        sender_company="启智（芜湖）智能机器人有限公司",
    )

    assert "Zhao Xin" in result
    assert "营销总监" in result
    assert (
        "启智（芜湖）智能机器人有限公司"
        in result
    )

    assert result.rstrip().endswith(
        "Best regards,\n"
        "Zhao Xin\n"
        "营销总监\n"
        "启智（芜湖）智能机器人有限公司"
    )