import json
import re
from collections import Counter
from datetime import datetime

from history_learning.models import (
    HistoricalEmail,
    StyleProfile,
)


STYLE_FIELDS = (
    "preferred_tone",
    "typical_length",
    "greeting_pattern",
    "closing_pattern",
    "structure_preferences",
    "wording_preferences",
)


STYLE_ANALYSIS_SYSTEM_PROMPT = """
You analyze writing style from previously sent business emails.

Your job is ONLY to learn writing habits such as:
- tone
- typical length
- greeting style
- closing style
- structure
- wording preferences

IMPORTANT SAFETY RULES:

1. Do NOT infer or learn commercial facts such as:
   prices, discounts, payment terms, Incoterms, inventory,
   delivery time, lead time, warranty, or availability.

2. Historical commercial information is context only
   and must never become a current fact.

3. Do NOT learn reply language or language choice from
   historical emails.

4. The customer-facing reply language for this product
   is always English, regardless of the language used in
   historical Sent emails or future incoming customer mail.

5. Historical French, German, Russian, Japanese, Korean,
   Chinese, Spanish, or other languages must NOT cause
   future replies to use those languages.

Return JSON only.

Use exactly these keys:

{
  "preferred_tone": "",
  "typical_length": "",
  "greeting_pattern": "",
  "closing_pattern": "",
  "structure_preferences": "",
  "wording_preferences": ""
}

Do not wrap the JSON in explanatory text.
""".strip()


def _non_empty_lines(
    body: str,
) -> list[str]:
    return [
        line.strip()
        for line in body.splitlines()
        if line.strip()
    ]


def compute_style_stats(
    sent_records: list[HistoricalEmail],
) -> dict[str, object]:
    """
    Compute simple writing-style statistics locally.

    No email content is sent anywhere by this function.
    """

    valid_records = [
        record
        for record in sent_records
        if record.body
        and record.body.strip()
    ]

    if not valid_records:
        return {
            "message_count": 0,
            "average_word_count": 0,
            "common_greeting": "",
            "common_closing": "",
        }

    word_counts: list[int] = []
    greetings: list[str] = []
    closings: list[str] = []

    for record in valid_records:
        body = record.body.strip()

        words = re.findall(
            r"\b[\w'-]+\b",
            body,
            flags=re.UNICODE,
        )

        word_counts.append(
            len(words)
        )

        lines = _non_empty_lines(
            body
        )

        if lines:
            greetings.append(
                lines[0]
            )

        if len(lines) >= 2:
            closings.append(
                lines[-1]
            )

    average_word_count = round(
        sum(word_counts)
        / len(word_counts),
        1,
    )

    common_greeting = ""

    if greetings:
        common_greeting = Counter(
            greeting.lower()
            for greeting in greetings
        ).most_common(1)[0][0]

    common_closing = ""

    if closings:
        common_closing = Counter(
            closing.lower()
            for closing in closings
        ).most_common(1)[0][0]

    return {
        "message_count": len(
            valid_records
        ),
        "average_word_count": (
            average_word_count
        ),
        "common_greeting": (
            common_greeting
        ),
        "common_closing": (
            common_closing
        ),
    }


def select_style_samples(
    sent_records: list[HistoricalEmail],
    max_samples: int = 20,
) -> list[HistoricalEmail]:
    """
    Select only a small set of the newest
    non-empty Sent emails.

    This prevents the full mailbox history
    from being sent to the LLM.
    """

    if max_samples <= 0:
        return []

    valid_records = [
        record
        for record in sent_records
        if record.body
        and record.body.strip()
    ]

    valid_records.sort(
        key=lambda item: item.sent_at,
        reverse=True,
    )

    return valid_records[
        :max_samples
    ]


def _build_sample_payload(
    records: list[HistoricalEmail],
) -> str:
    sections: list[str] = []

    for record in records:
        body = record.body.strip()[
            :4000
        ]

        sections.append(
            "\n".join(
                [
                    (
                        "Message-ID: "
                        f"{record.message_id}"
                    ),
                    (
                        "Sent-At: "
                        f"{record.sent_at.isoformat()}"
                    ),
                    (
                        "Subject: "
                        f"{record.subject}"
                    ),
                    "Body:",
                    body,
                ]
            )
        )

    return (
        "# Historical Sent Email Samples\n\n"
        + "\n\n---\n\n".join(
            sections
        )
    )


def _strip_json_fence(
    value: str,
) -> str:
    text = value.strip()

    fence_match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=(
            re.DOTALL
            | re.IGNORECASE
        ),
    )

    if fence_match:
        return fence_match.group(
            1
        ).strip()

    return text


def _parse_style_json(
    value: str,
) -> dict[str, str]:
    try:
        parsed = json.loads(
            _strip_json_fence(
                value
            )
        )
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError(
            "Style analysis returned invalid JSON"
        ) from exc

    if not isinstance(
        parsed,
        dict,
    ):
        raise ValueError(
            "Style analysis JSON must be an object"
        )

    result: dict[str, str] = {}

    for field_name in STYLE_FIELDS:
        field_value = parsed.get(
            field_name,
            "",
        )

        if field_value is None:
            field_value = ""

        if not isinstance(
            field_value,
            str,
        ):
            raise ValueError(
                "Style analysis fields "
                "must be strings"
            )

        result[
            field_name
        ] = field_value.strip()

    return result


def build_style_profile(
    provider,
    sent_records: list[HistoricalEmail],
    existing_overrides: (
        dict[str, str]
        | None
    ) = None,
) -> StyleProfile:
    """
    Build a style profile from a limited set
    of previously Sent emails.

    Language choice is intentionally NOT learned.
    Future customer-facing drafts remain English.
    """

    samples = select_style_samples(
        sent_records,
        max_samples=20,
    )

    if not samples:
        raise ValueError(
            "No Sent email samples available "
            "for style learning"
        )

    payload = _build_sample_payload(
        samples
    )

    raw_result = provider.generate_reply(
        skill_text=(
            STYLE_ANALYSIS_SYSTEM_PROMPT
        ),
        customer_email=payload,
    )

    style_data = _parse_style_json(
        raw_result
    )

    return StyleProfile(
        preferred_tone=style_data[
            "preferred_tone"
        ],
        typical_length=style_data[
            "typical_length"
        ],
        greeting_pattern=style_data[
            "greeting_pattern"
        ],
        closing_pattern=style_data[
            "closing_pattern"
        ],
        structure_preferences=style_data[
            "structure_preferences"
        ],
        wording_preferences=style_data[
            "wording_preferences"
        ],
        manual_overrides=dict(
            existing_overrides
            or {}
        ),
        updated_at=(
            datetime.now()
            .astimezone()
            .isoformat()
        ),
    )


def effective_style(
    profile: StyleProfile,
) -> dict[str, str]:
    """
    Return the style that should actually be used.

    Manual user edits have higher priority
    than automatically learned values.
    """

    result = {
        "preferred_tone": (
            profile.preferred_tone
        ),
        "typical_length": (
            profile.typical_length
        ),
        "greeting_pattern": (
            profile.greeting_pattern
        ),
        "closing_pattern": (
            profile.closing_pattern
        ),
        "structure_preferences": (
            profile.structure_preferences
        ),
        "wording_preferences": (
            profile.wording_preferences
        ),
    }

    for key, value in (
        profile.manual_overrides.items()
    ):
        if (
            key in result
            and isinstance(
                value,
                str,
            )
        ):
            result[key] = (
                value.strip()
            )

    return result
