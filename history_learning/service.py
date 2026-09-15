from datetime import datetime
from pathlib import Path

from history_learning.identity import customer_identity
from history_learning.imap_source import (
    discover_sent_mailbox,
    fetch_folder_raw_emails,
)
from history_learning.models import (
    HistoricalEmail,
    LearningSummary,
)
from history_learning.selection import (
    months_ago,
    parse_mail_datetime,
    select_recent_history,
)
from history_learning.store import HistoryStore
from history_learning.style import build_style_profile
from mail_reader.eligibility import (
    is_customer_email_candidate,
)
from mail_reader.parser import (
    ParsedEmail,
    parse_email,
)


def _parsed_to_historical(
    mail: ParsedEmail,
    mailbox: str,
    own_email: str,
) -> HistoricalEmail | None:
    """
    Convert one parsed email into a historical
    learning record.

    Returns None when the message is not suitable
    for history learning.

    This function does not modify the mailbox
    and does not send email.
    """

    normalized_mailbox = (
        mailbox.strip()
    )

    if (
        normalized_mailbox.upper()
        == "INBOX"
    ):
        direction = "incoming"

        if not is_customer_email_candidate(
            mail
        ):
            return None

    else:
        direction = "outgoing"

    message_id = (
        mail.message_id
        or ""
    ).strip()

    body = (
        mail.body
        or ""
    ).strip()

    if not message_id:
        return None

    if not body:
        return None

    sent_at = parse_mail_datetime(
        mail.date
    )

    if sent_at is None:
        return None

    (
        customer_email,
        company_domain,
    ) = customer_identity(
        mail=mail,
        direction=direction,
        own_email=own_email,
    )

    if not customer_email:
        return None

    return HistoricalEmail(
        message_id=message_id,
        mailbox=normalized_mailbox,
        direction=direction,
        sender=(
            mail.sender
            or ""
        ).strip(),
        recipients=(
            mail.recipients
            or ""
        ).strip(),
        subject=(
            mail.subject
            or ""
        ).strip(),
        sent_at=sent_at,
        body=body,
        customer_email=customer_email,
        company_domain=company_domain,
    )


def run_initial_learning(
    mail_config,
    provider,
    db_path: Path,
    now: datetime | None = None,
) -> LearningSummary:
    """
    Run the first manual mailbox-learning process.

    Default behavior:
    - recent six calendar months
    - maximum 1000 qualifying emails total
    - INBOX + Sent only
    - mailbox access remains read-only
    - system/security mail is excluded
    - Sent final messages are used for style learning
    - no Drafts are read
    - no customer email is ever sent
    """

    if now is None:
        now = (
            datetime.now()
            .astimezone()
        )

    cutoff = months_ago(
        now,
        6,
    )

    store = HistoryStore(
        db_path
    )
    store.initialize()

    raw_inbox = fetch_folder_raw_emails(
        config=mail_config,
        mailbox="INBOX",
        since=cutoff.date(),
        max_messages=1000,
    )

    sent_mailbox = (
        discover_sent_mailbox(
            mail_config
        )
    )

    if sent_mailbox is None:
        raw_sent = []
    else:
        raw_sent = (
            fetch_folder_raw_emails(
                config=mail_config,
                mailbox=sent_mailbox,
                since=cutoff.date(),
                max_messages=1000,
            )
        )

    scanned = (
        len(raw_inbox)
        + len(raw_sent)
    )

    skipped = 0
    failed = 0

    candidates: list[
        HistoricalEmail
    ] = []

    def process_raw_messages(
        raw_messages: list[bytes],
        mailbox: str,
    ) -> None:
        nonlocal skipped
        nonlocal failed

        for raw_email in raw_messages:
            try:
                parsed = parse_email(
                    raw_email
                )

                record = (
                    _parsed_to_historical(
                        mail=parsed,
                        mailbox=mailbox,
                        own_email=(
                            mail_config.email_user
                        ),
                    )
                )

                if record is None:
                    skipped += 1
                    continue

                candidates.append(
                    record
                )

            except Exception:
                # One malformed historical email
                # must not prevent later messages
                # from being learned.
                failed += 1

    process_raw_messages(
        raw_inbox,
        "INBOX",
    )

    if sent_mailbox is not None:
        process_raw_messages(
            raw_sent,
            sent_mailbox,
        )

    selected = select_recent_history(
        candidates,
        now=now,
        months=6,
        limit=1000,
    )

    # Messages may still have been returned by
    # the provider even though their exact Date
    # header lies outside the six-month window.
    skipped += (
        len(candidates)
        - len(selected)
    )

    learned = 0

    for record in selected:
        inserted = store.insert_email(
            record
        )

        if inserted:
            learned += 1
        else:
            # Message-ID already learned.
            skipped += 1

    warnings: list[str] = []

    style_profile_updated = False

    if sent_mailbox is None:
        warnings.append(
            "未找到已发送邮件文件夹，"
            "历史邮件索引已完成，"
            "但回复风格学习不完整。"
        )

    else:
        sent_records = (
            store.list_sent()
        )

        if sent_records:
            try:
                existing_profile = (
                    store.get_style_profile()
                )

                if existing_profile is None:
                    existing_overrides = {}
                else:
                    existing_overrides = dict(
                        existing_profile
                        .manual_overrides
                    )

                profile = (
                    build_style_profile(
                        provider=provider,
                        sent_records=sent_records,
                        existing_overrides=(
                            existing_overrides
                        ),
                    )
                )

                store.save_style_profile(
                    profile
                )

                style_profile_updated = (
                    True
                )

            except Exception as exc:
                failed += 1

                warnings.append(
                    "回复风格学习失败："
                    f"{exc}"
                )

        else:
            warnings.append(
                "未找到可用于学习回复风格的"
                "有效已发送邮件。"
            )

    finished_at = (
        now.isoformat()
    )

    state = {
        "initial_learning_completed": (
            "true"
        ),
        "initial_learning_finished_at": (
            finished_at
        ),
        "scanned_count": str(
            scanned
        ),
        "learned_count": str(
            learned
        ),
        "skipped_count": str(
            skipped
        ),
        "failed_count": str(
            failed
        ),
    }

    if sent_mailbox is not None:
        state[
            "last_sent_sync_at"
        ] = finished_at

    store.set_learning_state(
        state
    )

    return LearningSummary(
        scanned=scanned,
        learned=learned,
        skipped=skipped,
        failed=failed,
        sent_mailbox_found=(
            sent_mailbox is not None
        ),
        style_profile_updated=(
            style_profile_updated
        ),
        warning="\n".join(
            warnings
        ),
    )


def sync_sent_incremental(
    mail_config,
    provider,
    store: HistoryStore,
    now: datetime | None = None,
) -> LearningSummary:
    """
    Incrementally learn newly Sent final emails.

    Important:
    - reads Sent only
    - never reads Drafts
    - Message-ID prevents duplicate learning
    - only final messages actually found in Sent are learned
    - style is rebuilt once per successful batch
    - checkpoint advances only after style update succeeds
    """

    if now is None:
        now = (
            datetime.now()
            .astimezone()
        )

    store.initialize()

    state = (
        store.get_learning_state()
    )

    last_sync_value = (
        state.get(
            "last_sent_sync_at",
            "",
        )
        or ""
    ).strip()

    if last_sync_value:
        try:
            last_sync = (
                datetime.fromisoformat(
                    last_sync_value
                )
            )
        except ValueError:
            last_sync = months_ago(
                now,
                6,
            )
    else:
        last_sync = months_ago(
            now,
            6,
        )

    sent_mailbox = (
        discover_sent_mailbox(
            mail_config
        )
    )

    if sent_mailbox is None:
        return LearningSummary(
            scanned=0,
            learned=0,
            skipped=0,
            failed=0,
            sent_mailbox_found=False,
            style_profile_updated=False,
            warning=(
                "未找到已发送邮件文件夹，"
                "本次增量学习未执行。"
            ),
        )

    raw_sent = fetch_folder_raw_emails(
        config=mail_config,
        mailbox=sent_mailbox,
        since=last_sync.date(),
        max_messages=1000,
    )

    scanned = len(
        raw_sent
    )

    learned = 0
    skipped = 0
    failed = 0

    for raw_email in raw_sent:
        try:
            parsed = parse_email(
                raw_email
            )

            record = (
                _parsed_to_historical(
                    mail=parsed,
                    mailbox=sent_mailbox,
                    own_email=(
                        mail_config.email_user
                    ),
                )
            )

            if record is None:
                skipped += 1
                continue

            if store.email_exists(
                record.message_id
            ):
                skipped += 1
                continue

            inserted = store.insert_email(
                record
            )

            if inserted:
                learned += 1
            else:
                skipped += 1

        except Exception:
            failed += 1

    style_profile_updated = False

    if learned > 0:
        existing_profile = (
            store.get_style_profile()
        )

        if existing_profile is None:
            existing_overrides = {}
        else:
            existing_overrides = dict(
                existing_profile
                .manual_overrides
            )

        sent_records = (
            store.list_sent(
                limit=200,
            )
        )

        # Deliberately do NOT swallow this exception.
        #
        # If style rebuilding fails, newly inserted
        # Message-IDs remain safely deduplicated,
        # but last_sent_sync_at must NOT advance.
        profile = build_style_profile(
            provider=provider,
            sent_records=sent_records,
            existing_overrides=(
                existing_overrides
            ),
        )

        store.save_style_profile(
            profile
        )

        style_profile_updated = True

    store.set_learning_state(
        {
            "last_sent_sync_at": (
                now.isoformat()
            )
        }
    )

    warning = ""

    if failed:
        warning = (
            f"有 {failed} 封已发送邮件"
            "未能完成增量学习。"
        )

    return LearningSummary(
        scanned=scanned,
        learned=learned,
        skipped=skipped,
        failed=failed,
        sent_mailbox_found=True,
        style_profile_updated=(
            style_profile_updated
        ),
        warning=warning,
    )
