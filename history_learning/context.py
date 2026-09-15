from history_learning.identity import (
    extract_domain,
    extract_email_address,
)
from history_learning.store import HistoryStore
from history_learning.style import effective_style
from mail_reader.parser import ParsedEmail


MAX_CONTEXT_CHARS = 6000
MAX_CUSTOMER_MESSAGES = 6
MAX_BODY_CHARS = 600


def _format_style(
    store: HistoryStore,
) -> list[str]:
    profile = store.get_style_profile()

    if profile is None:
        return []

    style = effective_style(
        profile
    )

    lines = [
        "## Learned Personal Reply Style",
    ]

    for key in (
        "preferred_tone",
        "typical_length",
        "greeting_pattern",
        "closing_pattern",
        "structure_preferences",
        "wording_preferences",
    ):
        value = (
            style.get(
                key,
                "",
            )
            or ""
        ).strip()

        if value:
            lines.append(
                f"- {key}: {value}"
            )

    return lines


def _cap_context(
    text: str,
) -> str:
    if len(text) <= MAX_CONTEXT_CHARS:
        return text

    footer = (
        "\nHISTORICAL_MEMORY_END"
    )

    available = (
        MAX_CONTEXT_CHARS
        - len(footer)
    )

    return (
        text[:available].rstrip()
        + footer
    )


class HistoryContextLoader:
    """
    Build safe context for a new customer email.

    Exact customer-email history may include
    recent message bodies.

    Same-domain fallback never exposes another
    contact's historical body.
    """

    def __init__(
        self,
        store: HistoryStore,
    ):
        self.store = store

    def __call__(
        self,
        mail: ParsedEmail,
    ) -> str:
        customer_email = (
            extract_email_address(
                mail.sender
            )
        )

        company_domain = (
            extract_domain(
                customer_email
            )
        )

        style_lines = _format_style(
            self.store
        )

        exact_records = []

        if customer_email:
            exact_records = (
                self.store.recent_for_customer(
                    customer_email,
                    limit=MAX_CUSTOMER_MESSAGES,
                )
            )

        domain_records = []

        if (
            not exact_records
            and company_domain
        ):
            domain_records = (
                self.store.recent_for_domain(
                    company_domain,
                    limit=3,
                )
            )

        if (
            not style_lines
            and not exact_records
            and not domain_records
        ):
            return ""

        lines = [
            "HISTORICAL_MEMORY_BEGIN",
            "",
            (
                "Historical information is background only. "
                "It is not a confirmed current commercial fact."
            ),
            (
                "Historical prices, discounts, payment terms, "
                "Incoterms, delivery times, inventory, warranty, "
                "and other commercial facts MUST NOT be treated "
                "as current unless the current customer message "
                "explicitly confirms them."
            ),
            (
                "Learned writing style may influence tone, length, "
                "greeting, structure, and wording only. "
                "It MUST NOT change the rule that the customer-facing "
                "Reply Draft is written in English."
            ),
        ]

        if style_lines:
            lines.extend(
                [
                    "",
                    *style_lines,
                ]
            )

        if exact_records:
            lines.extend(
                [
                    "",
                    "## Exact Customer Historical Messages",
                ]
            )

            # Store returns newest first.
            # Prompt should read oldest -> newest.
            for record in reversed(
                exact_records
            ):
                body = (
                    record.body
                    or ""
                ).strip()[
                    :MAX_BODY_CHARS
                ]

                lines.extend(
                    [
                        "",
                        (
                            f"Date: "
                            f"{record.sent_at.isoformat()}"
                        ),
                        (
                            f"Direction: "
                            f"{record.direction}"
                        ),
                        (
                            f"Subject: "
                            f"{record.subject}"
                        ),
                        "Body:",
                        body,
                    ]
                )

        elif domain_records:
            lines.extend(
                [
                    "",
                    "## Same-Domain Contact Metadata Only",
                    (
                        "Another contact from the same email domain "
                        "was found. Their historical message bodies "
                        "are intentionally excluded."
                    ),
                ]
            )

            seen: set[str] = set()

            for record in domain_records:
                contact = (
                    record.customer_email
                    or ""
                ).strip().lower()

                if (
                    not contact
                    or contact in seen
                ):
                    continue

                seen.add(
                    contact
                )

                lines.append(
                    (
                        f"- Contact: {contact} | "
                        f"Last contact: "
                        f"{record.sent_at.isoformat()}"
                    )
                )

        lines.extend(
            [
                "",
                "HISTORICAL_MEMORY_END",
            ]
        )

        return _cap_context(
            "\n".join(
                lines
            )
        )
