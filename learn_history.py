from pathlib import Path

from history_learning.service import (
    run_initial_learning,
)
from llm.config import load_llm_config
from llm.factory import create_llm_provider
from mail_reader.config import load_mail_config


HISTORY_DB_PATH = Path(
    "runtime/history_learning.db"
)


def main():
    """
    Manually start the first history-learning run.

    This is intentionally separate from the normal
    production mail-processing entry point.

    Initial history learning must be explicitly
    triggered by the user.
    """

    mail_config = load_mail_config()

    llm_config = load_llm_config()

    provider = create_llm_provider(
        config=llm_config,
    )

    return run_initial_learning(
        mail_config=mail_config,
        provider=provider,
        db_path=HISTORY_DB_PATH,
    )


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
        "\nNo customer email was automatically sent."
    )
