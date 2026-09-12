import json
import urllib.error
from types import SimpleNamespace


def test_build_inquiry_notification_contains_mail_information():
    from wecom.notifier import (
        build_inquiry_notification,
    )

    mail = SimpleNamespace(
        sender="Emma Wilson <emma@example.com>",
        subject="RFQ for Model R2 - 9 Units",
    )

    message = build_inquiry_notification(
        mail
    )

    assert "New customer inquiry" in message
    assert (
        "Emma Wilson <emma@example.com>"
        in message
    )
    assert (
        "RFQ for Model R2 - 9 Units"
        in message
    )

    assert "AI analysis completed" in message
    assert "Reply draft saved to mailbox" in message
    assert (
        "Customer email was not automatically sent"
        in message
    )


def test_send_wecom_text_posts_expected_payload(
    monkeypatch,
):
    from wecom.notifier import (
        send_wecom_text,
    )

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            pass

        def read(self):
            return json.dumps(
                {
                    "errcode": 0,
                    "errmsg": "ok",
                }
            ).encode("utf-8")

    def fake_urlopen(
        request,
        timeout,
    ):
        captured["url"] = request.full_url
        captured["data"] = json.loads(
            request.data.decode("utf-8")
        )
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        "urllib.request.urlopen",
        fake_urlopen,
    )

    result = send_wecom_text(
        webhook_url=(
            "https://qyapi.weixin.qq.com/"
            "cgi-bin/webhook/send?key=fake-key"
        ),
        content="Test notification",
    )

    assert result is True

    assert captured["data"] == {
        "msgtype": "text",
        "text": {
            "content": "Test notification",
        },
    }

    assert captured["timeout"] == 10


def test_send_wecom_text_returns_false_on_network_error(
    monkeypatch,
):
    from wecom.notifier import (
        send_wecom_text,
    )

    def fake_urlopen(
        request,
        timeout,
    ):
        raise urllib.error.URLError(
            "network unavailable"
        )

    monkeypatch.setattr(
        "urllib.request.urlopen",
        fake_urlopen,
    )

    result = send_wecom_text(
        webhook_url=(
            "https://qyapi.weixin.qq.com/"
            "cgi-bin/webhook/send?key=fake-key"
        ),
        content="Test notification",
    )

    assert result is False
def test_send_wecom_text_returns_false_when_webhook_empty(
    monkeypatch,
):
    from wecom.notifier import (
        send_wecom_text,
    )

    def fake_urlopen(
        request,
        timeout,
    ):
        raise AssertionError(
            "Network must not be called"
        )

    monkeypatch.setattr(
        "urllib.request.urlopen",
        fake_urlopen,
    )

    result = send_wecom_text(
        webhook_url="",
        content="Test notification",
    )

    assert result is False