from datetime import datetime, timedelta, timezone

import pytest

from history_learning.models import (
    HistoricalEmail,
    StyleProfile,
)


def load_style_functions():
    try:
        from history_learning.style import (
            build_style_profile,
            compute_style_stats,
            effective_style,
            select_style_samples,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"history_learning.style is missing: {exc}"
        )

    return (
        compute_style_stats,
        select_style_samples,
        build_style_profile,
        effective_style,
    )


def make_sent(
    message_id: str,
    sent_at: datetime,
    body: str,
) -> HistoricalEmail:
    return HistoricalEmail(
        message_id=message_id,
        mailbox="Sent",
        direction="outgoing",
        sender="sales@example.cn",
        recipients="customer@example.com",
        subject="Re: Inquiry",
        sent_at=sent_at,
        body=body,
        customer_email="customer@example.com",
        company_domain="example.com",
    )


class FakeProvider:
    def __init__(
        self,
        result: str,
    ):
        self.result = result
        self.calls = []

    def generate_reply(
        self,
        skill_text: str,
        customer_email: str,
    ) -> str:
        self.calls.append(
            {
                "skill_text": skill_text,
                "customer_email": customer_email,
            }
        )

        return self.result


def test_compute_style_stats_uses_real_sent_content():
    (
        compute_style_stats,
        _,
        _,
        _,
    ) = load_style_functions()

    now = datetime(
        2026,
        9,
        14,
        tzinfo=timezone.utc,
    )

    records = [
        make_sent(
            "<m1@example.com>",
            now,
            (
                "Dear Pierre,\n\n"
                "Thank you for your inquiry.\n\n"
                "Best regards"
            ),
        ),
        make_sent(
            "<m2@example.com>",
            now + timedelta(minutes=1),
            (
                "Dear Alice,\n\n"
                "Thank you for your message. "
                "Please find our comments below. "
                "We will confirm the commercial "
                "details after internal review.\n\n"
                "Best regards"
            ),
        ),
        make_sent(
            "<m3@example.com>",
            now + timedelta(minutes=2),
            (
                "Dear David,\n\n"
                "Thanks for your inquiry. "
                "Please see the information below.\n\n"
                "Best regards"
            ),
        ),
    ]

    stats = compute_style_stats(
        records
    )

    assert stats["message_count"] == 3

    assert stats[
        "average_word_count"
    ] > 0

    assert stats[
        "common_greeting"
    ].lower().startswith(
        "dear"
    )

    assert (
        "best regards"
        in stats[
            "common_closing"
        ].lower()
    )


def test_style_samples_are_limited_to_20_newest():
    (
        _,
        select_style_samples,
        _,
        _,
    ) = load_style_functions()

    base = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    records = [
        make_sent(
            f"<m{index}@example.com>",
            base + timedelta(minutes=index),
            f"Email body {index}",
        )
        for index in range(25)
    ]

    samples = select_style_samples(
        records
    )

    assert len(samples) == 20

    assert (
        samples[0].message_id
        == "<m24@example.com>"
    )

    assert (
        samples[-1].message_id
        == "<m5@example.com>"
    )


def test_build_style_profile_parses_json_and_limits_samples():
    (
        _,
        _,
        build_style_profile,
        _,
    ) = load_style_functions()

    provider = FakeProvider(
        """
        {
          "preferred_tone":
            "professional, concise, friendly",
          "typical_length":
            "100-150 words",
          "greeting_pattern":
            "Dear + customer name",
          "closing_pattern":
            "Best regards",
          "structure_preferences":
            "answer questions in order",
          "wording_preferences":
            "avoid unsupported commitments"
        }
        """
    )

    base = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    records = [
        make_sent(
            f"<m{index}@example.com>",
            base + timedelta(minutes=index),
            (
                f"Dear Customer {index},\n\n"
                + ("A" * 5000)
                + "\n\nBest regards"
            ),
        )
        for index in range(25)
    ]

    profile = build_style_profile(
        provider=provider,
        sent_records=records,
    )

    assert (
        profile.preferred_tone
        == "professional, concise, friendly"
    )

    assert (
        profile.typical_length
        == "100-150 words"
    )

    assert len(
        provider.calls
    ) == 1

    payload = provider.calls[0][
        "customer_email"
    ]

    assert payload.count(
        "Message-ID:"
    ) <= 20

    # Each sample must be truncated before
    # being sent to the LLM.
    assert "A" * 4500 not in payload


def test_style_prompt_does_not_learn_reply_language():
    (
        _,
        _,
        build_style_profile,
        _,
    ) = load_style_functions()

    provider = FakeProvider(
        """
        {
          "preferred_tone": "professional",
          "typical_length": "short",
          "greeting_pattern": "Dear + name",
          "closing_pattern": "Best regards",
          "structure_preferences": "concise",
          "wording_preferences": "clear"
        }
        """
    )

    records = [
        make_sent(
            "<m1@example.com>",
            datetime(
                2026,
                9,
                1,
                tzinfo=timezone.utc,
            ),
            "Bonjour Pierre, merci. Cordialement",
        )
    ]

    build_style_profile(
        provider=provider,
        sent_records=records,
    )

    system_prompt = provider.calls[0][
        "skill_text"
    ].lower()

    assert "english" in system_prompt

    assert (
        "reply language"
        in system_prompt
        or "language choice"
        in system_prompt
    )


def test_manual_overrides_win_over_learned_style():
    (
        _,
        _,
        _,
        effective_style,
    ) = load_style_functions()

    profile = StyleProfile(
        preferred_tone="professional",
        typical_length="100-150 words",
        greeting_pattern="Dear + name",
        closing_pattern="Best regards",
        structure_preferences="answer in order",
        wording_preferences="clear",
        manual_overrides={
            "typical_length": "under 100 words",
            "preferred_tone": "friendly",
        },
    )

    style = effective_style(
        profile
    )

    assert (
        style["typical_length"]
        == "under 100 words"
    )

    assert (
        style["preferred_tone"]
        == "friendly"
    )

    assert (
        style["closing_pattern"]
        == "Best regards"
    )
