from pathlib import Path

from agent.foreign_trade_agent import run_foreign_trade_agent
from agent.result_parser import extract_reply_draft

from llm.base import LLMProvider
from llm.config import load_llm_config
from llm.factory import create_llm_provider

from mail_reader.agent_payload import build_agent_payload
from mail_reader.config import load_mail_config
from mail_reader.eligibility import (
    is_customer_email_candidate,
)
from mail_reader.pipeline import (
    read_latest_email,
    read_recent_emails,
)
from mail_reader.processed_store import (
    is_message_processed,
    mark_message_processed,
)

from mail_writer.reply_builder import build_reply_message
from mail_writer.draft_client import save_draft
from mail_writer.signature import apply_sender_signature

from wecom.config import load_wecom_config
from wecom.notifier import (
    build_inquiry_notification,
    send_wecom_text,
)


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

BATCH_LIMIT = 20


def _make_history_filename(
    mail,
) -> str:
    """
    Build a filesystem-safe history filename
    from the email Message-ID.
    """

    message_id = getattr(
        mail,
        "message_id",
        "",
    ) or "unknown-message"

    safe_name = "".join(
        char
        if char.isalnum()
        or char in ("-", "_")
        else "_"
        for char in message_id
    )

    safe_name = safe_name.strip("_")

    if not safe_name:
        safe_name = "unknown-message"

    return f"{safe_name}.md"


def save_analysis_history(
    mail,
    result: str,
    result_path: Path,
) -> Path:
    """
    Save an independent analysis history record
    for one customer email.

    History directory:

        result/history/

    Each email gets its own Markdown file.
    """

    history_dir = (
        result_path.parent / "history"
    )

    history_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    history_path = (
        history_dir
        / _make_history_filename(mail)
    )

    sender = getattr(
        mail,
        "sender",
        "",
    )

    subject = getattr(
        mail,
        "subject",
        "",
    )

    date = getattr(
        mail,
        "date",
        "",
    )

    message_id = getattr(
        mail,
        "message_id",
        "",
    )

    history_content = (
        "# Foreign Trade Email Analysis\n\n"
        f"Message-ID: {message_id}\n\n"
        f"From: {sender}\n\n"
        f"Subject: {subject}\n\n"
        f"Date: {date}\n\n"
        "---\n\n"
        f"{result}"
    )

    history_path.write_text(
        history_content,
        encoding="utf-8",
    )

    return history_path


def create_reply_draft(
    mail,
    agent_result: str,
    mail_config,
    sender_email: str,
) -> str:
    """
    Extract the customer-facing Reply Draft,
    apply the configured sender signature,
    build a reply email,
    and save it to Drafts.

    This function NEVER sends email.
    """

    reply_body = extract_reply_draft(
        agent_result
    )

    sender_name = getattr(
        mail_config,
        "sender_name",
        "",
    )

    sender_title = getattr(
        mail_config,
        "sender_title",
        "",
    )

    sender_company = getattr(
        mail_config,
        "sender_company",
        "",
    )

    reply_body = apply_sender_signature(
        draft=reply_body,
        sender_name=sender_name,
        sender_title=sender_title,
        sender_company=sender_company,
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


def process_mail(
    mail,
    provider: LLMProvider,
    mail_config,
    skill_path: Path,
    result_path: Path,
    processed_store_path: Path = PROCESSED_STORE_PATH,
    create_draft: bool = False,
    wecom_config=None,
    history_context_loader=None,
) -> str:
    """
    Process one ParsedEmail.

    Workflow:

        1. Check Message-ID
        2. Skip already processed email
        3. Build AI input
        4. Run Foreign Trade Agent
        5. Save latest analysis result
        6. Save independent history record
        7. Optionally create reply draft
        8. Mark Message-ID processed
        9. Optionally notify WeCom

    Important:

        - Duplicate email:
            no AI request
            no duplicate draft

        - Draft creation failure:
            Message-ID is NOT recorded

        - WeCom notification happens only
          after draft creation and Message-ID marking

        - WeCom failure must NOT break
          the email processing workflow

        - Email is NEVER automatically sent
    """

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

    history_context = ""

    if history_context_loader is not None:
        try:
            history_context = (
                history_context_loader(
                    mail
                )
            )
        except Exception:
            # History learning is optional.
            # Failure must never block normal
            # customer email processing.
            history_context = ""

    if history_context:
        customer_email = build_agent_payload(
            mail,
            history_context=history_context,
        )
    else:
        # Preserve the original call shape when
        # history is unavailable or disabled.
        #
        # History learning is an optional enhancement
        # and must never break the existing mail flow.
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

    # Keep the latest analysis for convenience.
    result_path.write_text(
        result,
        encoding="utf-8",
    )

    # Also keep an independent history record
    # for this specific customer email.
    save_analysis_history(
        mail=mail,
        result=result,
        result_path=result_path,
    )

    if create_draft:
        create_reply_draft(
            mail=mail,
            agent_result=result,
            mail_config=mail_config,
            sender_email=mail_config.email_user,
        )

        # Record the Message-ID only AFTER
        # the draft was successfully saved.
        mark_message_processed(
            message_id=message_id,
            store_path=processed_store_path,
        )

        # WeCom is only a secondary notification channel.
        #
        # The order is intentionally:
        #
        # draft saved
        #     ↓
        # Message-ID recorded
        #     ↓
        # WeCom notification
        #
        # Any WeCom failure must stay isolated
        # from the email workflow.
        if (
            wecom_config is not None
            and getattr(
                wecom_config,
                "enabled",
                False,
            )
        ):
            try:
                notification = (
                    build_inquiry_notification(
                        mail
                    )
                )

                send_wecom_text(
                    webhook_url=getattr(
                        wecom_config,
                        "webhook_url",
                        "",
                    ),
                    content=notification,
                )

            except Exception:
                # WeCom notification is optional.
                # Never fail or repeat customer email
                # processing because WeCom is unavailable.
                pass

    return result


def run_once(
    provider: LLMProvider,
    mail_config,
    skill_path: Path,
    result_path: Path,
    create_draft: bool = False,
    processed_store_path: Path = PROCESSED_STORE_PATH,
) -> str:
    """
    Single-email compatibility workflow.

    Reads only the latest email.
    """

    mail = read_latest_email(
        mail_config
    )

    return process_mail(
        mail=mail,
        provider=provider,
        mail_config=mail_config,
        skill_path=skill_path,
        result_path=result_path,
        processed_store_path=processed_store_path,
        create_draft=create_draft,
    )


def run_batch(
    provider: LLMProvider,
    mail_config,
    skill_path: Path,
    result_path: Path,
    processed_store_path: Path = PROCESSED_STORE_PATH,
    limit: int = BATCH_LIMIT,
    create_draft: bool = True,
    wecom_config=None,
) -> dict[str, int]:
    """
    Process multiple recent emails.

    Workflow for every email:

        recent email
            |
            v
        customer candidate?
            |
        NO  -> skip
            |
        YES
            |
            v
        process_mail()
            |
            +-> already processed -> skip
            |
            +-> new customer mail
            |       |
            |       +-> AI analysis
            |       +-> latest result
            |       +-> history record
            |       +-> draft
            |       +-> optional WeCom notification
            |
            +-> exception -> failed

    One failed email does not stop later emails.

    Returns:

        {
            "total": int,
            "processed": int,
            "skipped": int,
            "failed": int,
        }

    For the current version, "skipped" includes:

        - already processed messages
        - system/security/verification/non-customer messages
    """

    mails = read_recent_emails(
        config=mail_config,
        limit=limit,
    )

    summary = {
        "total": len(mails),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
    }

    for mail in mails:
        # Customer Email Gate
        #
        # Known system/security/verification messages
        # must never be sent to the AI or turned into
        # reply drafts.
        if not is_customer_email_candidate(
            mail
        ):
            summary["skipped"] += 1
            continue

        try:
            process_kwargs = {
                "mail": mail,
                "provider": provider,
                "mail_config": mail_config,
                "skill_path": skill_path,
                "result_path": result_path,
                "processed_store_path": processed_store_path,
                "create_draft": create_draft,
            }

            # Keep backward compatibility when
            # WeCom is not configured.
            if wecom_config is not None:
                process_kwargs[
                    "wecom_config"
                ] = wecom_config

            result = process_mail(
                **process_kwargs
            )

        except Exception:
            summary["failed"] += 1
            continue

        if result == SKIPPED_ALREADY_PROCESSED:
            summary["skipped"] += 1
        else:
            summary["processed"] += 1

    return summary


def main() -> str:
    """
    Single-email entry point.

    Kept for backward compatibility
    and existing tests.
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


def batch_main(
    wecom_config=None,
) -> dict[str, int]:
    """
    Production batch entry point.

    Scan recent emails,
    ignore known non-customer messages,
    skip already processed Message-IDs,
    process new customer emails,
    save independent analysis history,
    create reply drafts,
    optionally notify WeCom,
    and return a summary.

    Email is NEVER automatically sent.
    """

    mail_config = load_mail_config()

    llm_config = load_llm_config()

    provider = create_llm_provider(
        config=llm_config,
    )

    batch_kwargs = {
        "provider": provider,
        "mail_config": mail_config,
        "skill_path": SKILL_PATH,
        "result_path": RESULT_PATH,
        "processed_store_path": PROCESSED_STORE_PATH,
        "limit": BATCH_LIMIT,
        "create_draft": True,
    }

    # Keep old behavior unchanged when
    # WeCom is not configured.
    if wecom_config is not None:
        batch_kwargs[
            "wecom_config"
        ] = wecom_config

    return run_batch(
        **batch_kwargs
    )


def run_production() -> dict[str, int]:
    """
    Production entry point.

    Load optional WeCom configuration
    and run the normal batch workflow.

    If WECOM_WEBHOOK_URL is missing,
    WeCom remains disabled and email
    processing continues normally.
    """

    wecom_config = load_wecom_config()

    return batch_main(
        wecom_config=wecom_config,
    )


if __name__ == "__main__":
    summary = run_production()

    print(
        "\n=== Foreign Trade Digital Employee ===\n"
    )

    print(
        "Batch processing completed."
    )

    print(
        f"Total scanned: {summary['total']}"
    )

    print(
        f"Processed:     {summary['processed']}"
    )

    print(
        f"Skipped:       {summary['skipped']}"
    )

    print(
        f"Failed:        {summary['failed']}"
    )

    print(
        "\nReply draft creation: ENABLED"
    )

    print(
        "IMPORTANT: Replies were saved as drafts only."
    )

    print(
        "No email was automatically sent."
    )