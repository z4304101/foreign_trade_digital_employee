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