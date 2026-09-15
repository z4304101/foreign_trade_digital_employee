from pathlib import Path

from history_learning.reply_baseline import (
    seed_processed_store_from_history,
)
from history_learning.service import (
    run_initial_learning,
)
from history_learning.store import HistoryStore
from llm.config import load_llm_config
from llm.factory import create_llm_provider
from mail_reader.config import load_mail_config


HISTORY_DB_PATH = Path(
    "runtime/history_learning.db"
)

PROCESSED_STORE_PATH = Path(
    "runtime/processed_message_ids.txt"
)


def main():
    """
    Manually start the first history-learning run.

    Initial learning is explicitly triggered
    by the user.

    After learning succeeds, all historical
    incoming Message-IDs are added to the
    production processed-message baseline.

    Therefore:

        historical INBOX
            -> learn only
            -> never create a new reply draft

        future INBOX mail
            -> remains eligible for processing
    """

    mail_config = load_mail_config()

    llm_config = load_llm_config()

    provider = create_llm_provider(
        config=llm_config,
    )

    summary = run_initial_learning(
        mail_config=mail_config,
        provider=provider,
        db_path=HISTORY_DB_PATH,
    )

    store = HistoryStore(
        HISTORY_DB_PATH
    )
    store.initialize()

    seed_processed_store_from_history(
        store=store,
        processed_store_path=(
            PROCESSED_STORE_PATH
        ),
    )

    return summary


if __name__ == "__main__":
    summary = main()

    print(
        "\n=== History Learning ===\n"
    )

    print(
        f"Scanned:       {summary.scanned}"
    )

    print(
        f"Learned:       {summary.learned}"
    )

    print(
        f"Skipped:       {summary.skipped}"
    )

    print(
        f"Failed:        {summary.failed}"
    )

    print(
        "Sent mailbox:  "
        + (
            "FOUND"
            if summary.sent_mailbox_found
            else "NOT FOUND"
        )
    )

    print(
        "Style updated: "
        + (
            "YES"
            if summary.style_profile_updated
            else "NO"
        )
    )

    if summary.warning:
        print(
            f"Warning:       {summary.warning}"
        )

    print(
        "\nHistorical inbox mail was "
        "added to the reply baseline."
    )

    print(
        "No customer email was automatically sent."
    )
