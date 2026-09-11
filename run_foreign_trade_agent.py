from pathlib import Path

from agent.foreign_trade_agent import run_foreign_trade_agent
from agent.result_parser import extract_reply_draft

from llm.base import LLMProvider
from llm.config import load_llm_config
from llm.factory import create_llm_provider

from mail_reader.agent_payload import build_agent_payload
from mail_reader.config import load_mail_config
from mail_reader.pipeline import read_latest_email
from mail_reader.processed_store import (
    is_message_processed,
    mark_message_processed,
)

from mail_writer.reply_builder import build_reply_message
from mail_writer.draft_client import save_draft


SKILL_PATH = Path(
    "skills/foreign-trade-reply/SKILL.md"
)

RESULT_PATH = Path(
    "result/latest_reply.md"
)

PROCESSED_STORE_PATH = Path(
    "runtime/processed_message_ids.txt"
)

SKIPPED_ALREADY_PROCESSED = (
    "SKIPPED_ALREADY_PROCESSED"
)


def create_reply_draft(
    mail,
    agent_result: str,
    mail_config,
    sender_email: str,
) -> str:
    """
    Extract the customer-facing reply from the validated
    agent result, build an email reply, and save it to Drafts.

    This function DOES NOT send email.
    """

    reply_body = extract_reply_draft(
        agent_result
    )

    message = build_reply_message(
        mail=mail,
        sender_email=sender_email,
        reply_body=reply_body,
    )

    drafts_mailbox = save_draft(
        config=mail_config,
        message=message,
    )

    return drafts_mailbox


def run_once(
    provider: LLMProvider,
    mail_config,
    skill_path: Path,
    result_path: Path,
    create_draft: bool = False,
    processed_store_path: Path = PROCESSED_STORE_PATH,
) -> str:
    """
    Process the latest customer email once.

    Workflow:

        1. Read latest email
        2. Check Message-ID
        3. Skip if already processed
        4. Build agent payload
        5. Run Foreign Trade Agent
        6. Save full analysis result
        7. Optionally create a reply draft
        8. Mark Message-ID processed only after
           the draft is saved successfully

    create_draft=False:
        analysis only

    create_draft=True:
        analysis + save reply to Drafts

    Email is NEVER automatically sent.
    """

    mail = read_latest_email(
        mail_config
    )

    message_id = getattr(
        mail,
        "message_id",
        None,
    )

    if is_message_processed(
        message_id=message_id,
        store_path=processed_store_path,
    ):
        return SKIPPED_ALREADY_PROCESSED

    customer_email = build_agent_payload(
        mail
    )

    result = run_foreign_trade_agent(
        provider=provider,
        skill_path=skill_path,
        customer_email=customer_email,
    )

    result_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_path.write_text(
        result,
        encoding="utf-8",
    )

    if create_draft:
        create_reply_draft(
            mail=mail,
            agent_result=result,
            mail_config=mail_config,
            sender_email=mail_config.email_user,
        )

        # IMPORTANT:
        # Only mark the message as processed AFTER
        # the draft has been saved successfully.
        mark_message_processed(
            message_id=message_id,
            store_path=processed_store_path,
        )

    return result


def main() -> str:
    """
    Main application entry point.

    Production workflow:

        latest customer email
            ↓
        Message-ID duplicate check
            ↓
        already processed?
          YES → skip
          NO  ↓
        DeepSeek analysis
            ↓
        Output Gate
            ↓
        save full analysis
            ↓
        extract Reply Draft
            ↓
        build email reply
            ↓
        save to mailbox Drafts
            ↓
        record Message-ID as processed

    No email is automatically sent.
    Human approval is still required.
    """

    mail_config = load_mail_config()

    llm_config = load_llm_config()

    provider = create_llm_provider(
        config=llm_config,
    )

    return run_once(
        provider=provider,
        mail_config=mail_config,
        skill_path=SKILL_PATH,
        result_path=RESULT_PATH,
        create_draft=True,
    )


if __name__ == "__main__":
    result = main()

    if result == SKIPPED_ALREADY_PROCESSED:
        print(
            "\n=== Foreign Trade Agent ===\n"
        )

        print(
            "Latest email has already been processed."
        )

        print(
            "No AI request was made."
        )

        print(
            "No duplicate draft was created."
        )

    else:
        print(
            "\n=== Foreign Trade Agent Result ===\n"
        )

        print(result)

        print(
            "\nAnalysis saved to:",
            RESULT_PATH.resolve(),
        )

        print(
            "\nReply draft creation: ENABLED"
        )

        print(
            "IMPORTANT: The reply was saved as a draft only."
        )

        print(
            "No email was automatically sent."
        )

        print(
            "Message-ID recorded as processed."
        )