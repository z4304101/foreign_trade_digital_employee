from types import SimpleNamespace


def test_customer_rfq_is_eligible():
    from mail_reader.eligibility import (
        is_customer_email_candidate,
    )

    mail = SimpleNamespace(
        sender=(
            "David Miller "
            "<david@nova-automation.com>"
        ),
        subject="RFQ for Model R2 - 8 Units",
    )

    assert (
        is_customer_email_candidate(mail)
        is True
    )


def test_customer_inquiry_is_eligible():
    from mail_reader.eligibility import (
        is_customer_email_candidate,
    )

    mail = SimpleNamespace(
        sender=(
            "Michael Brown "
            "<michael@customer.com>"
        ),
        subject="Inquiry for Model R2",
    )

    assert (
        is_customer_email_candidate(mail)
        is True
    )


def test_netease_security_email_is_not_eligible():
    from mail_reader.eligibility import (
        is_customer_email_candidate,
    )

    mail = SimpleNamespace(
        sender=(
            "网易邮箱账号安全 "
            "<safe@service.netease.com>"
        ),
        subject="新设备登录提醒",
    )

    assert (
        is_customer_email_candidate(mail)
        is False
    )


def test_apple_verification_email_is_not_eligible():
    from mail_reader.eligibility import (
        is_customer_email_candidate,
    )

    mail = SimpleNamespace(
        sender=(
            "Apple <appleid@id.apple.com>"
        ),
        subject=(
            "Verify your Apple Account "
            "email address."
        ),
    )

    assert (
        is_customer_email_candidate(mail)
        is False
    )


def test_noreply_sender_is_not_eligible():
    from mail_reader.eligibility import (
        is_customer_email_candidate,
    )

    mail = SimpleNamespace(
        sender=(
            "System "
            "<noreply@example.com>"
        ),
        subject="Account Notification",
    )

    assert (
        is_customer_email_candidate(mail)
        is False
    )


def test_normal_reply_is_still_eligible():
    from mail_reader.eligibility import (
        is_customer_email_candidate,
    )

    mail = SimpleNamespace(
        sender=(
            "David Miller "
            "<david@nova-automation.com>"
        ),
        subject="Re: RFQ for Model R2",
    )

    assert (
        is_customer_email_candidate(mail)
        is True
    )