from pathlib import Path


SKILL_PATH = Path(
    "skills/foreign-trade-reply/SKILL.md"
)


def test_skill_distinguishes_customer_person_from_company():
    skill_text = SKILL_PATH.read_text(
        encoding="utf-8",
    )

    assert (
        "Customer = human contact person"
        in skill_text
    )

    assert (
        "Company = organization"
        in skill_text
    )

    assert (
        "Daniel Martin"
        in skill_text
    )

    assert (
        "EuroTech Automation"
        in skill_text
    )


def test_skill_prefers_current_signature_for_customer_identity():
    skill_text = SKILL_PATH.read_text(
        encoding="utf-8",
    )

    skill_text_lower = skill_text.lower()

    assert (
        "current message signature"
        in skill_text_lower
    )

    assert (
        "do not use the company name as customer"
        in skill_text_lower
    )