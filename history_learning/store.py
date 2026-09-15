import json
import sqlite3
from datetime import datetime
from pathlib import Path

from history_learning.models import (
    HistoricalEmail,
    StyleProfile,
)


class HistoryStore:
    def __init__(
        self,
        db_path: Path,
    ):
        self.db_path = Path(
            db_path
        )

    def _connect(
        self,
    ) -> sqlite3.Connection:
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(
            self.db_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def initialize(
        self,
    ) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS email_history (
                    message_id TEXT PRIMARY KEY,
                    mailbox TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipients TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    body TEXT NOT NULL,
                    customer_email TEXT NOT NULL,
                    customer_name TEXT NOT NULL DEFAULT '',
                    company_name TEXT NOT NULL DEFAULT '',
                    company_domain TEXT NOT NULL DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS
                    idx_email_history_customer
                ON email_history(
                    customer_email,
                    sent_at
                );

                CREATE INDEX IF NOT EXISTS
                    idx_email_history_domain
                ON email_history(
                    company_domain,
                    sent_at
                );

                CREATE TABLE IF NOT EXISTS style_profile (
                    id INTEGER PRIMARY KEY
                        CHECK (id = 1),
                    preferred_tone TEXT NOT NULL DEFAULT '',
                    typical_length TEXT NOT NULL DEFAULT '',
                    greeting_pattern TEXT NOT NULL DEFAULT '',
                    closing_pattern TEXT NOT NULL DEFAULT '',
                    structure_preferences TEXT NOT NULL DEFAULT '',
                    wording_preferences TEXT NOT NULL DEFAULT '',
                    manual_overrides_json TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS customer_memory (
                    customer_email TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL DEFAULT '',
                    company_name TEXT NOT NULL DEFAULT '',
                    company_domain TEXT NOT NULL DEFAULT '',
                    last_contact_at TEXT NOT NULL DEFAULT '',
                    recent_products_json TEXT NOT NULL DEFAULT '[]',
                    recent_topics_json TEXT NOT NULL DEFAULT '[]',
                    last_thread_summary TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS learning_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _row_to_email(
        row: sqlite3.Row,
    ) -> HistoricalEmail:
        return HistoricalEmail(
            message_id=row[
                "message_id"
            ],
            mailbox=row[
                "mailbox"
            ],
            direction=row[
                "direction"
            ],
            sender=row[
                "sender"
            ],
            recipients=row[
                "recipients"
            ],
            subject=row[
                "subject"
            ],
            sent_at=datetime.fromisoformat(
                row[
                    "sent_at"
                ]
            ),
            body=row[
                "body"
            ],
            customer_email=row[
                "customer_email"
            ],
            customer_name=row[
                "customer_name"
            ],
            company_name=row[
                "company_name"
            ],
            company_domain=row[
                "company_domain"
            ],
        )

    def insert_email(
        self,
        record: HistoricalEmail,
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO email_history (
                    message_id,
                    mailbox,
                    direction,
                    sender,
                    recipients,
                    subject,
                    sent_at,
                    body,
                    customer_email,
                    customer_name,
                    company_name,
                    company_domain
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.message_id,
                    record.mailbox,
                    record.direction,
                    record.sender,
                    record.recipients,
                    record.subject,
                    record.sent_at.isoformat(),
                    record.body,
                    record.customer_email,
                    record.customer_name,
                    record.company_name,
                    record.company_domain,
                ),
            )

            inserted = (
                cursor.rowcount == 1
            )

            if (
                inserted
                and record.customer_email
            ):
                connection.execute(
                    """
                    INSERT INTO customer_memory (
                        customer_email,
                        customer_name,
                        company_name,
                        company_domain,
                        last_contact_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(customer_email)
                    DO UPDATE SET
                        customer_name =
                            CASE
                                WHEN excluded.customer_name != ''
                                THEN excluded.customer_name
                                ELSE customer_memory.customer_name
                            END,
                        company_name =
                            CASE
                                WHEN excluded.company_name != ''
                                THEN excluded.company_name
                                ELSE customer_memory.company_name
                            END,
                        company_domain =
                            CASE
                                WHEN excluded.company_domain != ''
                                THEN excluded.company_domain
                                ELSE customer_memory.company_domain
                            END,
                        last_contact_at =
                            CASE
                                WHEN excluded.last_contact_at >
                                     customer_memory.last_contact_at
                                THEN excluded.last_contact_at
                                ELSE customer_memory.last_contact_at
                            END
                    """,
                    (
                        record.customer_email,
                        record.customer_name,
                        record.company_name,
                        record.company_domain,
                        record.sent_at.isoformat(),
                    ),
                )

            return inserted

    def email_exists(
        self,
        message_id: str,
    ) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM email_history
                WHERE message_id = ?
                LIMIT 1
                """,
                (
                    message_id,
                ),
            ).fetchone()

            return row is not None

    def list_incoming_message_ids(
        self,
    ) -> list[str]:
        """
        Return Message-IDs learned from historical INBOX mail.

        These IDs form the initial reply baseline:
        historical incoming mail may be used for learning,
        but must never be treated as a new inquiry later.
        """

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT message_id
                FROM email_history
                WHERE direction = 'incoming'
                  AND message_id != ''
                ORDER BY sent_at ASC
                """
            ).fetchall()

        return [
            row["message_id"]
            for row in rows
            if row["message_id"]
        ]


    def list_sent(
        self,
        limit: int | None = None,
    ) -> list[HistoricalEmail]:
        query = """
            SELECT *
            FROM email_history
            WHERE direction = 'outgoing'
            ORDER BY sent_at DESC
        """

        parameters: tuple = ()

        if limit is not None:
            query += " LIMIT ?"

            parameters = (
                limit,
            )

        with self._connect() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

        return [
            self._row_to_email(
                row
            )
            for row in rows
        ]

    def recent_for_customer(
        self,
        customer_email: str,
        limit: int = 6,
    ) -> list[HistoricalEmail]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM email_history
                WHERE lower(customer_email)
                    = lower(?)
                ORDER BY sent_at DESC
                LIMIT ?
                """,
                (
                    customer_email,
                    limit,
                ),
            ).fetchall()

        return [
            self._row_to_email(
                row
            )
            for row in rows
        ]

    def recent_for_domain(
        self,
        company_domain: str,
        limit: int = 3,
    ) -> list[HistoricalEmail]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM email_history
                WHERE lower(company_domain)
                    = lower(?)
                ORDER BY sent_at DESC
                LIMIT ?
                """,
                (
                    company_domain,
                    limit,
                ),
            ).fetchall()

        return [
            self._row_to_email(
                row
            )
            for row in rows
        ]

    def get_style_profile(
        self,
    ) -> StyleProfile | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM style_profile
                WHERE id = 1
                """
            ).fetchone()

        if row is None:
            return None

        try:
            manual_overrides = json.loads(
                row[
                    "manual_overrides_json"
                ]
            )
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            manual_overrides = {}

        if not isinstance(
            manual_overrides,
            dict,
        ):
            manual_overrides = {}

        return StyleProfile(
            preferred_tone=row[
                "preferred_tone"
            ],
            typical_length=row[
                "typical_length"
            ],
            greeting_pattern=row[
                "greeting_pattern"
            ],
            closing_pattern=row[
                "closing_pattern"
            ],
            structure_preferences=row[
                "structure_preferences"
            ],
            wording_preferences=row[
                "wording_preferences"
            ],
            manual_overrides=manual_overrides,
            updated_at=row[
                "updated_at"
            ],
        )

    def save_style_profile(
        self,
        profile: StyleProfile,
    ) -> None:
        overrides_json = json.dumps(
            profile.manual_overrides,
            ensure_ascii=False,
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO style_profile (
                    id,
                    preferred_tone,
                    typical_length,
                    greeting_pattern,
                    closing_pattern,
                    structure_preferences,
                    wording_preferences,
                    manual_overrides_json,
                    updated_at
                )
                VALUES (
                    1, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(id)
                DO UPDATE SET
                    preferred_tone =
                        excluded.preferred_tone,
                    typical_length =
                        excluded.typical_length,
                    greeting_pattern =
                        excluded.greeting_pattern,
                    closing_pattern =
                        excluded.closing_pattern,
                    structure_preferences =
                        excluded.structure_preferences,
                    wording_preferences =
                        excluded.wording_preferences,
                    manual_overrides_json =
                        excluded.manual_overrides_json,
                    updated_at =
                        excluded.updated_at
                """,
                (
                    profile.preferred_tone,
                    profile.typical_length,
                    profile.greeting_pattern,
                    profile.closing_pattern,
                    profile.structure_preferences,
                    profile.wording_preferences,
                    overrides_json,
                    profile.updated_at,
                ),
            )

    def save_manual_style_overrides(
        self,
        overrides: dict[str, str],
    ) -> None:
        profile = (
            self.get_style_profile()
        )

        overrides_json = json.dumps(
            overrides,
            ensure_ascii=False,
        )

        with self._connect() as connection:
            if profile is None:
                connection.execute(
                    """
                    INSERT INTO style_profile (
                        id,
                        manual_overrides_json
                    )
                    VALUES (
                        1,
                        ?
                    )
                    """,
                    (
                        overrides_json,
                    ),
                )

            else:
                connection.execute(
                    """
                    UPDATE style_profile
                    SET manual_overrides_json = ?
                    WHERE id = 1
                    """,
                    (
                        overrides_json,
                    ),
                )

    def get_learning_state(
        self,
    ) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT key, value
                FROM learning_state
                """
            ).fetchall()

        return {
            row[
                "key"
            ]: row[
                "value"
            ]
            for row in rows
        }

    def set_learning_state(
        self,
        values: dict[str, str],
    ) -> None:
        with self._connect() as connection:
            for key, value in values.items():
                connection.execute(
                    """
                    INSERT INTO learning_state (
                        key,
                        value
                    )
                    VALUES (?, ?)
                    ON CONFLICT(key)
                    DO UPDATE SET
                        value = excluded.value
                    """,
                    (
                        str(
                            key
                        ),
                        str(
                            value
                        ),
                    ),
                )
