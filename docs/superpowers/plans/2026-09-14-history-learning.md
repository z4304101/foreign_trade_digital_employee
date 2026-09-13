# History Learning and Customer Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local, read-only history-learning engine that learns the user’s email reply style from the last 6 months of INBOX + Sent mail, keeps per-customer history, incrementally learns newly sent final emails, and supplies safe historical context to the existing draft-only reply workflow.

**Architecture:** Add a focused `history_learning/` package around the existing mail reader and agent pipeline. SQLite stores local history, style profile, customer identity, and checkpoints. The existing `run_foreign_trade_agent.py` workflow remains authoritative for customer handling and is extended only through an optional history-context loader; if history learning is missing or fails, current email processing continues unchanged.

**Tech Stack:** Python 3, stdlib `imaplib`, `email`, `sqlite3`, existing LLMProvider abstraction, pytest, existing 163 IMAP support.

**Spec:** `docs/superpowers/specs/2026-09-14-history-learning-design.md`

## Global Constraints

- Initial learning window is the most recent 6 calendar months.
- Learn at most 1000 valid historical emails; if fewer exist, learn all available emails in range.
- Initial learning reads only INBOX and Sent; Drafts, Trash, Spam and other folders are excluded.
- Historical mailbox reads MUST use read-only selection and MUST NOT alter read/unread flags, move, delete, or send mail.
- System/security/verification/no-reply messages continue to be excluded using existing eligibility logic.
- AI-generated drafts are never learned directly; only final messages found in Sent are eligible for ongoing style learning.
- Message-ID is the deduplication key.
- Historical commercial data is background only and MUST NOT become current confirmed facts.
- Existing language behavior is non-negotiable: detect the customer’s original language, show Chinese translation, reply in the customer’s original language, and show Chinese back-translation.
- Existing Output Gate and `skills/foreign-trade-reply/SKILL.md` remain higher priority than learned style/history.
- Customer mail is still saved as a draft only. No implementation in this plan may add SMTP sending or any automatic customer send action.
- History-learning failures MUST NOT cause duplicate drafts, duplicate WeCom notifications, or block the existing production email workflow.
- Current 76-test regression baseline must remain green; new tests are added on top.
- V1 does not add GUI, PySide6, PyInstaller, Inno Setup, Gmail/Outlook/QQ support, vector DB, cloud history storage, multi-profile support, or model fine-tuning.

---

## File Structure

New package:

```text
history_learning/
├── __init__.py           # package marker
├── models.py             # dataclasses shared by history-learning modules
├── selection.py          # six-month filtering and 1000-message cap
├── imap_source.py        # Sent discovery and read-only historical folder reads
├── identity.py           # customer email/domain identity helpers
├── store.py              # SQLite schema and persistence/query API
├── style.py              # style statistics, LLM style summary, manual overrides
├── context.py            # safe limited context loader for new inquiries
└── service.py            # initial learning and incremental Sent sync orchestration
```

Existing files modified:

```text
mail_reader/parser.py
mail_reader/agent_payload.py
skills/foreign-trade-reply/SKILL.md
run_foreign_trade_agent.py
```

New development entry point:

```text
learn_history.py
```

New tests:

```text
tests/test_history_models.py
tests/test_history_selection.py
tests/test_history_imap_source.py
tests/test_history_store.py
tests/test_history_style.py
tests/test_history_context.py
tests/test_history_service.py
tests/test_history_production_wiring.py
```

---

### Task 1: Preserve recipient metadata and define history models

**Files:**
- Create: `history_learning/__init__.py`
- Create: `history_learning/models.py`
- Modify: `mail_reader/parser.py`
- Test: `tests/test_history_models.py`
- Modify test: `tests/test_email_parser.py`

**Interfaces:**
- Produces: `HistoricalEmail`, `StyleProfile`, `LearningSummary` dataclasses.
- Extends: `mail_reader.parser.ParsedEmail` with `recipients: str = ""` while preserving all existing constructor compatibility.

- [ ] **Step 1: Write failing parser and model tests**

Add tests equivalent to:

```python
from datetime import datetime, timezone

from history_learning.models import HistoricalEmail, LearningSummary
from mail_reader.parser import parse_email


def test_parse_email_preserves_to_header():
    raw = (
        b"From: Pierre <pierre@example.com>\r\n"
        b"To: sales@example.cn\r\n"
        b"Subject: Hello\r\n"
        b"Message-ID: <m1@example.com>\r\n"
        b"\r\nBody"
    )
    mail = parse_email(raw)
    assert mail.recipients == "sales@example.cn"


def test_historical_email_carries_direction_and_identity():
    record = HistoricalEmail(
        message_id="<m1@example.com>",
        mailbox="Sent",
        direction="outgoing",
        sender="sales@example.cn",
        recipients="pierre@example.com",
        subject="Re: Hello",
        sent_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        body="Thanks",
        customer_email="pierre@example.com",
        company_domain="example.com",
    )
    assert record.direction == "outgoing"
    assert record.customer_email == "pierre@example.com"
```

`HistoricalEmail` must contain exactly these public fields:

```python
message_id: str
mailbox: str
direction: str
sender: str
recipients: str
subject: str
sent_at: datetime
body: str
customer_email: str
customer_name: str = ""
company_name: str = ""
company_domain: str = ""
```

`StyleProfile` fields:

```python
preferred_tone: str = ""
typical_length: str = ""
greeting_pattern: str = ""
closing_pattern: str = ""
structure_preferences: str = ""
wording_preferences: str = ""
manual_overrides: dict[str, str] = field(default_factory=dict)
updated_at: str = ""
```

`LearningSummary` fields:

```python
scanned: int
learned: int
skipped: int
failed: int
sent_mailbox_found: bool
style_profile_updated: bool
warning: str = ""
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python -m pytest tests/test_history_models.py tests/test_email_parser.py -v
```

Expected: FAIL because `history_learning.models` and `ParsedEmail.recipients` do not yet exist.

- [ ] **Step 3: Implement the minimal model and parser changes**

In `mail_reader/parser.py`, add `recipients` to the dataclass with a default and parse the `To` header:

```python
@dataclass
class ParsedEmail:
    sender: str
    subject: str
    date: str
    body: str
    reply_to: str = ""
    message_id: str = ""
    references: str = ""
    recipients: str = ""
```

Inside `parse_email()`:

```python
recipients = str(message.get("To", "")).strip()
...
return ParsedEmail(
    ...,
    references=references,
    recipients=recipients,
)
```

Create the three dataclasses in `history_learning/models.py` using `@dataclass(frozen=True)` for `HistoricalEmail` and `LearningSummary`, and mutable `@dataclass` for `StyleProfile` because manual overrides are edited locally.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_history_models.py tests/test_email_parser.py -v
```

Expected: PASS.

- [ ] **Step 5: Run the existing parser/reply metadata regression tests**

Run:

```bash
python -m pytest tests/test_email_parser.py tests/test_email_reply_metadata.py tests/test_agent_payload.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add history_learning mail_reader/parser.py tests/test_history_models.py tests/test_email_parser.py
git commit -m "feat: add history learning models"
```

---

### Task 2: Implement exact six-month selection and the 1000-message cap

**Files:**
- Create: `history_learning/selection.py`
- Test: `tests/test_history_selection.py`

**Interfaces:**
- Produces: `parse_mail_datetime(value: str) -> datetime | None`
- Produces: `months_ago(now: datetime, months: int) -> datetime`
- Produces: `select_recent_history(records: list[HistoricalEmail], now: datetime, months: int = 6, limit: int = 1000) -> list[HistoricalEmail]`

- [ ] **Step 1: Write failing date-boundary and cap tests**

Use fixed timezone-aware datetimes. Cover:

```python
def test_six_month_cutoff_is_calendar_based():
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
    assert months_ago(now, 6) == datetime(2026, 3, 14, 12, tzinfo=timezone.utc)


def test_month_end_is_clamped():
    now = datetime(2026, 8, 31, 12, tzinfo=timezone.utc)
    assert months_ago(now, 6) == datetime(2026, 2, 28, 12, tzinfo=timezone.utc)


def test_history_keeps_only_latest_1000_inside_window():
    records = make_records(count=1005, starting_at=datetime(2026, 9, 1, tzinfo=timezone.utc))
    selected = select_recent_history(records, now=datetime(2026, 9, 14, tzinfo=timezone.utc))
    assert len(selected) == 1000
    assert selected == sorted(selected, key=lambda item: item.sent_at)
```

Also test that a message one second before the exact six-month cutoff is excluded.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
python -m pytest tests/test_history_selection.py -v
```

Expected: FAIL because the functions do not exist.

- [ ] **Step 3: Implement calendar-month subtraction and selection**

Implementation shape:

```python
import calendar
from datetime import datetime
from email.utils import parsedate_to_datetime


def parse_mail_datetime(value: str) -> datetime | None:
    if not value or not value.strip():
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return parsed


def months_ago(now: datetime, months: int) -> datetime:
    total = now.year * 12 + (now.month - 1) - months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(now.day, calendar.monthrange(year, month)[1])
    return now.replace(year=year, month=month, day=day)


def select_recent_history(records, now, months=6, limit=1000):
    cutoff = months_ago(now, months)
    eligible = [item for item in records if item.sent_at >= cutoff]
    eligible.sort(key=lambda item: item.sent_at, reverse=True)
    selected = eligible[:limit]
    selected.sort(key=lambda item: item.sent_at)
    return selected
```

- [ ] **Step 4: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_selection.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add history_learning/selection.py tests/test_history_selection.py
git commit -m "feat: select six months of email history"
```

---

### Task 3: Discover Sent and read historical folders without changing mailbox state

**Files:**
- Create: `history_learning/imap_source.py`
- Test: `tests/test_history_imap_source.py`

**Interfaces:**
- Consumes: `MailConfig`, existing `mail_reader.imap_client._send_client_id`.
- Produces: `discover_sent_mailbox(config: MailConfig) -> str | None`
- Produces: `fetch_folder_raw_emails(config: MailConfig, mailbox: str, since: date, max_messages: int = 1000) -> list[bytes]`

- [ ] **Step 1: Write failing Sent-discovery tests**

Mock `imaplib.IMAP4_SSL` and cover these responses:

```python
[
    b'(\\HasNoChildren \\Sent) "/" "Sent"',
    b'(\\HasNoChildren) "/" "INBOX"',
]
```

Expected `discover_sent_mailbox(...) == "Sent"`.

Fallback case:

```python
[
    b'(\\HasNoChildren) "/" "INBOX"',
    b'(\\HasNoChildren) "/" "Sent Messages"',
]
```

Expected `"Sent Messages"`.

No-match case returns `None`.

- [ ] **Step 2: Write failing read-only fetch tests**

The fake IMAP client must record calls. Assert:

```python
client.select.assert_called_once_with("Sent", readonly=True)
client.fetch.assert_any_call(message_id, "(BODY.PEEK[])")
```

Also assert the server search contains a `SINCE` criterion based on the supplied date and that only the newest `max_messages` IDs are fetched.

- [ ] **Step 3: Run focused tests and verify RED**

```bash
python -m pytest tests/test_history_imap_source.py -v
```

Expected: FAIL because `history_learning.imap_source` does not exist.

- [ ] **Step 4: Implement Sent discovery**

Parse IMAP `LIST` rows without assuming the folder is always literally named `Sent`:

```python
COMMON_SENT_NAMES = (
    "sent",
    "sent messages",
    "sent mail",
    "已发送",
    "已发送邮件",
)
```

First choose a row containing the `\\Sent` flag (case-insensitive). If no special-use row exists, decode the final quoted mailbox token and compare its normalized name to `COMMON_SENT_NAMES`.

- [ ] **Step 5: Implement read-only folder fetching**

The function must:

```python
client = imaplib.IMAP4_SSL(config.imap_host, config.imap_port)
client.login(config.email_user, config.auth_code)
_send_client_id(client)
client.select(mailbox, readonly=True)
client.search(None, "SINCE", since.strftime("%d-%b-%Y"))
```

Then take only the newest `max_messages` message sequence IDs and fetch each with `BODY.PEEK[]`. Always `logout()` in `finally`.

- [ ] **Step 6: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_imap_source.py -v
```

Expected: PASS, including explicit assertions that `readonly=True` and `BODY.PEEK[]` are used.

- [ ] **Step 7: Run existing IMAP regression tests**

```bash
python -m pytest tests/test_imap_connection.py tests/test_fetch_latest_mail.py tests/test_fetch_recent_mail.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add history_learning/imap_source.py tests/test_history_imap_source.py
git commit -m "feat: read historical mailboxes safely"
```

---

### Task 4: Add customer identity helpers and the local SQLite store

**Files:**
- Create: `history_learning/identity.py`
- Create: `history_learning/store.py`
- Test: `tests/test_history_store.py`

**Interfaces:**
- Produces: `extract_email_address(header: str) -> str`
- Produces: `extract_domain(address: str) -> str`
- Produces: `customer_identity(mail: ParsedEmail, direction: str, own_email: str) -> tuple[str, str]`
- Produces: `HistoryStore(db_path: Path)`.

`HistoryStore` public methods:

```python
initialize() -> None
insert_email(record: HistoricalEmail) -> bool
email_exists(message_id: str) -> bool
list_sent(limit: int | None = None) -> list[HistoricalEmail]
recent_for_customer(customer_email: str, limit: int = 6) -> list[HistoricalEmail]
recent_for_domain(company_domain: str, limit: int = 3) -> list[HistoricalEmail]
get_style_profile() -> StyleProfile | None
save_style_profile(profile: StyleProfile) -> None
save_manual_style_overrides(overrides: dict[str, str]) -> None
get_learning_state() -> dict[str, str]
set_learning_state(values: dict[str, str]) -> None
```

- [ ] **Step 1: Write failing identity tests**

Cover:

```python
assert extract_email_address("Pierre <PIERRE@Example.com>") == "pierre@example.com"
assert extract_domain("pierre@example.com") == "example.com"
```

Incoming identity uses sender. Outgoing identity uses the first recipient that is not equal to the configured own mailbox address.

- [ ] **Step 2: Write failing SQLite tests**

Use pytest `tmp_path`. Assert:

```python
store = HistoryStore(tmp_path / "history.db")
store.initialize()
assert store.insert_email(record) is True
assert store.insert_email(record) is False
assert store.email_exists(record.message_id) is True
```

The second insert MUST NOT duplicate the Message-ID.

Also test `recent_for_customer()` orders newest first and `recent_for_domain()` never returns another domain.

- [ ] **Step 3: Run tests and verify RED**

```bash
python -m pytest tests/test_history_store.py -v
```

Expected: FAIL because identity/store APIs do not exist.

- [ ] **Step 4: Implement identity helpers**

Use `email.utils.getaddresses`/`parseaddr`; normalize to lowercase. Do not invent a name or company from an email username. Domain is only the substring after `@` when a valid address exists.

- [ ] **Step 5: Implement SQLite schema**

`HistoryStore.initialize()` creates these tables with `CREATE TABLE IF NOT EXISTS`:

```sql
CREATE TABLE email_history (
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

CREATE TABLE style_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    preferred_tone TEXT NOT NULL DEFAULT '',
    typical_length TEXT NOT NULL DEFAULT '',
    greeting_pattern TEXT NOT NULL DEFAULT '',
    closing_pattern TEXT NOT NULL DEFAULT '',
    structure_preferences TEXT NOT NULL DEFAULT '',
    wording_preferences TEXT NOT NULL DEFAULT '',
    manual_overrides_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE customer_memory (
    customer_email TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL DEFAULT '',
    company_name TEXT NOT NULL DEFAULT '',
    company_domain TEXT NOT NULL DEFAULT '',
    last_contact_at TEXT NOT NULL DEFAULT '',
    recent_products_json TEXT NOT NULL DEFAULT '[]',
    recent_topics_json TEXT NOT NULL DEFAULT '[]',
    last_thread_summary TEXT NOT NULL DEFAULT ''
);

CREATE TABLE learning_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Add indexes on `email_history(customer_email, sent_at)` and `email_history(company_domain, sent_at)`.

`insert_email()` uses `INSERT OR IGNORE` and returns `cursor.rowcount == 1`. When inserted, upsert `customer_memory` with the latest contact time and identity fields that are actually known. Do not synthesize commercial facts.

- [ ] **Step 6: Implement style/state persistence**

Serialize `manual_overrides` with `json.dumps(..., ensure_ascii=False)`. When `save_style_profile()` updates the automatic fields, preserve any existing manual override JSON unless the caller explicitly supplies it.

- [ ] **Step 7: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_store.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add history_learning/identity.py history_learning/store.py tests/test_history_store.py
git commit -m "feat: store learned email history locally"
```

---

### Task 5: Build the reply-style profile with local statistics and limited LLM samples

**Files:**
- Create: `history_learning/style.py`
- Test: `tests/test_history_style.py`

**Interfaces:**
- Consumes: `LLMProvider`, `HistoricalEmail`, `StyleProfile`.
- Produces: `compute_style_stats(sent_records: list[HistoricalEmail]) -> dict[str, object]`
- Produces: `select_style_samples(sent_records: list[HistoricalEmail], max_samples: int = 20) -> list[HistoricalEmail]`
- Produces: `build_style_profile(provider: LLMProvider, sent_records: list[HistoricalEmail], existing_overrides: dict[str, str] | None = None) -> StyleProfile`
- Produces: `effective_style(profile: StyleProfile) -> dict[str, str]`

- [ ] **Step 1: Write failing local-statistics tests**

Use three outgoing emails and assert average word count, common first-line greeting, and common closing are derived locally. The test data must include one short and one long reply so `typical_length` is not a hard-coded constant.

- [ ] **Step 2: Write failing sample-limit and LLM parsing tests**

A fake provider returns exactly:

```json
{
  "preferred_tone": "professional, concise, friendly",
  "typical_length": "100-150 words",
  "greeting_pattern": "Dear + customer name",
  "closing_pattern": "Best regards",
  "structure_preferences": "answer questions in order",
  "wording_preferences": "avoid unsupported commitments"
}
```

Assert no more than 20 message bodies are included in the fake provider’s input, and assert manual overrides win:

```python
profile.manual_overrides = {"typical_length": "under 100 words"}
assert effective_style(profile)["typical_length"] == "under 100 words"
```

- [ ] **Step 3: Run focused tests and verify RED**

```bash
python -m pytest tests/test_history_style.py -v
```

Expected: FAIL.

- [ ] **Step 4: Implement local statistics and representative sampling**

Sampling rule: sort Sent messages newest first, take at most 20 non-empty messages, and cap each body at 4000 characters before putting it in the LLM input. Do not send all 1000 historical emails to the model.

- [ ] **Step 5: Implement the style-analysis LLM request**

Use the existing provider interface without changing `LLMProvider`:

```python
result = provider.generate_reply(
    skill_text=STYLE_ANALYSIS_SYSTEM_PROMPT,
    customer_email=style_sample_payload,
)
```

The system prompt MUST require JSON only, forbid commercial-fact inference, and state that style analysis is about writing habits only. Strip optional Markdown code fences before `json.loads()`.

If the LLM output is invalid JSON, raise `ValueError`; the caller decides whether learning is complete. Do not silently invent a style profile.

- [ ] **Step 6: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_style.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add history_learning/style.py tests/test_history_style.py
git commit -m "feat: learn user email reply style"
```

---

### Task 6: Orchestrate the first manual history-learning run

**Files:**
- Create: `history_learning/service.py`
- Test: `tests/test_history_service.py`

**Interfaces:**
- Produces: `run_initial_learning(mail_config, provider, db_path: Path, now: datetime | None = None) -> LearningSummary`
- Internal helper: `_parsed_to_historical(mail, mailbox, own_email) -> HistoricalEmail | None`

- [ ] **Step 1: Write failing happy-path service test**

Mock the IMAP source to return INBOX and Sent raw messages. Include:

- one valid customer INBOX mail,
- one system/security INBOX mail,
- one valid Sent final reply,
- one message older than six months.

Assert:

```python
summary.learned == 2
summary.skipped == 2
summary.failed == 0
summary.sent_mailbox_found is True
summary.style_profile_updated is True
```

Assert the store contains only the valid in-range customer incoming mail and valid final Sent reply.

- [ ] **Step 2: Write failing missing-Sent test**

When `discover_sent_mailbox()` returns `None`, INBOX indexing must still complete. Expected:

```python
summary.sent_mailbox_found is False
summary.style_profile_updated is False
assert "已发送" in summary.warning
```

The learning state must record that initial scanning completed but style learning is incomplete.

- [ ] **Step 3: Write failing per-message parse isolation test**

One malformed historical message must increment `failed` and not prevent later valid messages from being learned.

- [ ] **Step 4: Run focused tests and verify RED**

```bash
python -m pytest tests/test_history_service.py -v
```

Expected: FAIL.

- [ ] **Step 5: Implement raw-message conversion and filtering**

For INBOX:

- parse with existing `parse_email()`;
- reject with existing `is_customer_email_candidate()`;
- derive customer identity from sender.

For Sent:

- require non-empty `Message-ID`;
- require non-empty body;
- derive customer from recipients, excluding `mail_config.email_user`;
- do not read Drafts at all.

Use `parse_mail_datetime()` and skip messages with an unparseable date rather than assigning today’s date.

- [ ] **Step 6: Implement initial learning orchestration**

Algorithm:

```python
now = now or datetime.now().astimezone()
cutoff = months_ago(now, 6)
raw_inbox = fetch_folder_raw_emails(mail_config, "INBOX", cutoff.date(), max_messages=1000)
sent_mailbox = discover_sent_mailbox(mail_config)
raw_sent = [] if sent_mailbox is None else fetch_folder_raw_emails(
    mail_config, sent_mailbox, cutoff.date(), max_messages=1000
)
```

Parse both sets, collect valid `HistoricalEmail` records, then call `select_recent_history(..., limit=1000)` across the combined list so the total cap is 1000, not 1000 per folder. Insert records in chronological order.

If at least one Sent record exists, build and save the style profile once after all records are inserted.

Only after all database writes succeed, set:

```text
initial_learning_completed=true
initial_learning_finished_at=<ISO timestamp>
last_sent_sync_at=<ISO timestamp>
scanned_count=<n>
learned_count=<n>
skipped_count=<n>
failed_count=<n>
```

If style analysis fails, keep indexed email history but do not mark `style_profile_updated=True`; surface the failure to the caller so the UI/CLI cannot falsely say style learning finished.

- [ ] **Step 7: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_service.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add history_learning/service.py tests/test_history_service.py
git commit -m "feat: add initial mailbox learning service"
```

---

### Task 7: Build safe customer-history context and protect multilingual behavior

**Files:**
- Create: `history_learning/context.py`
- Modify: `mail_reader/agent_payload.py`
- Modify: `skills/foreign-trade-reply/SKILL.md`
- Test: `tests/test_history_context.py`
- Modify test: `tests/test_agent_payload.py`
- Modify test: `tests/test_foreign_trade_agent.py`

**Interfaces:**
- Produces: `HistoryContextLoader(store: HistoryStore)` callable object.
- `HistoryContextLoader.__call__(mail: ParsedEmail) -> str`
- Extends: `build_agent_payload(mail: ParsedEmail, history_context: str = "") -> str`

- [ ] **Step 1: Write failing exact-customer context tests**

Store 10 historical messages for one customer. Assert the context contains no more than the most recent 6 messages (3 incoming/outgoing rounds maximum) and never exceeds 6000 characters.

The context format MUST include explicit boundaries:

```text
HISTORICAL_MEMORY_BEGIN
...
HISTORICAL_MEMORY_END
```

and the warning:

```text
Historical information is background only. It is not a confirmed current commercial fact.
```

- [ ] **Step 2: Write failing domain-fallback safety test**

If there is no exact customer-email history but another contact uses the same company domain, do NOT inject that other contact’s full email bodies. Domain fallback may include only safe company/contact metadata such as known contact email and last-contact date. This prevents one person’s old prices or promises leaking into another person’s reply.

- [ ] **Step 3: Write failing agent-payload compatibility test**

Without history:

```python
assert build_agent_payload(mail) == previous_expected_payload
```

With history, assert the historical block is outside the `UNTRUSTED_CUSTOMER_EMAIL_BEGIN/END` current-message block and is clearly labelled historical.

- [ ] **Step 4: Add multilingual regression assertions before changing the skill**

In a skill-text test, assert all four requirements remain present:

```text
MUST detect the customer's original language.
MUST provide a Chinese translation
SHOULD reply in the customer's original language.
MUST provide a Chinese back-translation
```

Also assert the required headings still include:

```text
## Customer Language
## Chinese Translation
## Reply Draft
## Chinese Back-Translation
## Send Status
```

- [ ] **Step 5: Run focused tests and verify RED where appropriate**

```bash
python -m pytest tests/test_history_context.py tests/test_agent_payload.py tests/test_foreign_trade_agent.py -v
```

Expected: new history-context tests FAIL; existing behavior remains green.

- [ ] **Step 6: Implement `HistoryContextLoader`**

Exact email match:

- load effective style profile;
- load most recent customer history, capped at 6 messages and 6000 characters;
- format oldest-to-newest inside the history block.

Domain-only fallback:

- include only metadata, never another contact’s full body.

No database/no match:

- return `""`.

- [ ] **Step 7: Extend `build_agent_payload()` compatibly**

Signature:

```python
def build_agent_payload(mail: ParsedEmail, history_context: str = "") -> str:
```

If `history_context` is empty, preserve current payload structure. If non-empty, append a separate section after `UNTRUSTED_CUSTOMER_EMAIL_END`:

```text
# Personal Style and Historical Context

<history_context>
```

- [ ] **Step 8: Strengthen SKILL.md for the new history block without changing language behavior**

Add rules stating that content inside `HISTORICAL_MEMORY_BEGIN/END` is historical background only and MUST NOT populate current `Key Information` unless the current message confirms it. Learned style may influence tone/length/structure, but MUST NOT override safety rules, original-language reply behavior, Chinese translation, or Chinese back-translation.

Do not remove or rename any existing required output heading.

- [ ] **Step 9: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_context.py tests/test_agent_payload.py tests/test_foreign_trade_agent.py -v
```

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add history_learning/context.py mail_reader/agent_payload.py skills/foreign-trade-reply/SKILL.md tests/test_history_context.py tests/test_agent_payload.py tests/test_foreign_trade_agent.py
git commit -m "feat: add safe learned context to replies"
```

---

### Task 8: Add automatic incremental learning from newly sent final emails

**Files:**
- Modify: `history_learning/service.py`
- Modify: `history_learning/store.py`
- Test: `tests/test_history_service.py`

**Interfaces:**
- Produces: `sync_sent_incremental(mail_config, provider, store: HistoryStore, now: datetime | None = None) -> LearningSummary`

- [ ] **Step 1: Write failing incremental dedupe test**

Preload one Sent Message-ID in SQLite, return that same raw Sent message plus one new Sent message from the mocked mailbox, then assert:

```python
summary.learned == 1
store.email_exists(old_id) is True
store.email_exists(new_id) is True
```

The style provider must be called exactly once for the batch, not once per message.

- [ ] **Step 2: Write failing checkpoint test**

If the style rebuild/provider raises, `last_sent_sync_at` must remain unchanged. Already-inserted Message-IDs may remain safely stored because deduplication prevents repeated learning on retry.

- [ ] **Step 3: Run focused tests and verify RED**

```bash
python -m pytest tests/test_history_service.py -v
```

Expected: FAIL on missing incremental sync.

- [ ] **Step 4: Implement incremental fetch**

Read `last_sent_sync_at`. Search Sent from that calendar date with read-only IMAP. Parse candidate messages and rely on `store.email_exists(message_id)` for exact dedupe.

Only final Sent messages are considered; Drafts are never opened.

- [ ] **Step 5: Update style once per successful batch**

When at least one new Sent record is inserted, rebuild the profile from `store.list_sent(limit=200)` using the existing style builder. The 200-record local read is only to produce representative statistics/samples; the style module still sends at most 20 capped samples to the LLM.

Only after history writes and style save succeed, update `last_sent_sync_at` to `now.isoformat()`.

- [ ] **Step 6: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_service.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add history_learning/service.py history_learning/store.py tests/test_history_service.py
git commit -m "feat: learn from newly sent final replies"
```

---

### Task 9: Wire history context into production without breaking existing mail flow

**Files:**
- Modify: `run_foreign_trade_agent.py`
- Create: `learn_history.py`
- Test: `tests/test_history_production_wiring.py`
- Modify test: `tests/test_batch_runner.py`

**Interfaces:**
- Adds optional parameter to `process_mail(...)`: `history_context_loader=None`
- Adds optional parameter to `run_batch(...)`: `history_context_loader=None`
- Adds constant: `HISTORY_DB_PATH = Path("runtime/history_learning.db")`
- Adds CLI entry point: `learn_history.main() -> LearningSummary`

- [ ] **Step 1: Write failing process-mail context wiring test**

Pass a fake loader returning `"STYLE/HISTORY"` and monkeypatch `run_foreign_trade_agent`. Assert the user payload received by the agent contains the historical context exactly once.

- [ ] **Step 2: Write failing history-loader failure-isolation test**

A fake loader raises `RuntimeError`. Assert `process_mail()` still runs the existing agent, still creates the draft, still marks the Message-ID processed, and still follows existing WeCom ordering. The historical-context exception must degrade to an empty context, not fail the customer email.

- [ ] **Step 3: Write failing production incremental-sync isolation test**

When initial learning has completed but `sync_sent_incremental()` raises, production batch processing must still execute. This satisfies the requirement that learning failure never blocks normal drafts.

- [ ] **Step 4: Run focused tests and verify RED**

```bash
python -m pytest tests/test_history_production_wiring.py tests/test_batch_runner.py -v
```

Expected: FAIL on missing optional wiring.

- [ ] **Step 5: Modify `process_mail()` and `run_batch()` compatibly**

Before `build_agent_payload()`:

```python
history_context = ""
if history_context_loader is not None:
    try:
        history_context = history_context_loader(mail)
    except Exception:
        history_context = ""

customer_email = build_agent_payload(
    mail,
    history_context=history_context,
)
```

Pass the optional loader through `run_batch()` only when supplied, matching the project’s current backward-compatibility pattern used for WeCom.

- [ ] **Step 6: Wire production history only when initialized**

`run_production()` loads mail config, LLM config/provider, WeCom config, and checks whether `runtime/history_learning.db` exists and `initial_learning_completed == "true"`.

If initialized:

1. construct `HistoryStore`;
2. try `sync_sent_incremental(...)` inside an isolated `try/except`;
3. construct `HistoryContextLoader(store)`;
4. call `run_batch(...)` with the loader.

If not initialized, call the existing batch workflow without a history loader. Do not force first-time history scanning from production; the initial scan remains user-triggered.

- [ ] **Step 7: Create `learn_history.py` development/manual entry point**

`main()`:

```python
mail_config = load_mail_config()
llm_config = load_llm_config()
provider = create_llm_provider(llm_config)
summary = run_initial_learning(
    mail_config=mail_config,
    provider=provider,
    db_path=Path("runtime/history_learning.db"),
)
return summary
```

When run as a script, print only non-secret counts/status. Never print mailbox auth code, API key, Webhook, or raw historical email bodies.

- [ ] **Step 8: Run focused tests and verify GREEN**

```bash
python -m pytest tests/test_history_production_wiring.py tests/test_batch_runner.py -v
```

Expected: PASS.

- [ ] **Step 9: Run the complete automated regression suite**

```bash
python -m pytest tests -v
```

Expected: all previous tests plus all new history-learning tests PASS with zero failures/errors.

- [ ] **Step 10: Commit**

```bash
git add run_foreign_trade_agent.py learn_history.py tests/test_history_production_wiring.py tests/test_batch_runner.py
git commit -m "feat: wire history learning into production"
```

---

### Task 10: Real 163 mailbox acceptance test and safety verification

**Files:**
- No code changes unless the real test exposes a defect.
- Runtime-only: `runtime/history_learning.db` (must remain ignored/uncommitted).

**Interfaces:**
- Validates the completed V1 against a real 163 mailbox.

- [ ] **Step 1: Verify Git ignores the local learning database and secrets**

Run:

```bash
git check-ignore -v .env runtime/history_learning.db
git ls-files .env runtime/history_learning.db
git status --short
```

Expected: `.env` and `runtime/history_learning.db` are ignored/not tracked; working tree contains only intentional source/test changes.

- [ ] **Step 2: Run the initial history-learning command once**

```bash
python learn_history.py
```

Expected output contains only safe summary fields such as:

```text
Scanned: <n>
Learned: <n>
Skipped: <n>
Failed: <n>
Sent mailbox found: True
Style profile updated: True
```

Verify the process does not change read/unread status and does not create/send customer email.

- [ ] **Step 3: Inspect the local learning state without exposing secrets**

Use a small local Python diagnostic to print only:

```text
initial_learning_completed
learned email count
sent email count
style profile non-empty fields
customer count
```

Do not print raw historical bodies in screenshots shared externally.

- [ ] **Step 4: Test an existing historical customer**

Send a new inquiry from an address that exists in the learned history. Run production once:

```bash
python run_foreign_trade_agent.py
```

Verify:

- customer original language is detected;
- Chinese translation is present in analysis;
- `Reply Draft` is in the customer’s original language;
- Chinese back-translation is present;
- draft recipient is the customer address;
- wording resembles the learned user style without copying old commercial facts;
- draft is saved only;
- WeCom notification occurs after successful draft handling;
- no customer email is automatically sent.

- [ ] **Step 5: Test a new customer with no history**

Send a new inquiry from an unseen address/domain. Verify normal agent behavior continues and no other customer’s message body/commercial history appears in the draft.

- [ ] **Step 6: Test incremental learning from a human-edited final Sent email**

Open one generated draft, manually edit it, then send it yourself from 163. Run production again. Verify the Sent Message-ID enters `email_history` once and the style profile update timestamp changes.

Run production a second time and verify the same Sent Message-ID is not learned again.

- [ ] **Step 7: Re-run full regression after real-mail fixes, if any**

```bash
python -m pytest tests -v
```

Expected: zero failures/errors.

- [ ] **Step 8: Final Git safety check**

```bash
git status --short
git ls-files .env runtime/history_learning.db
git grep -n "qyapi.weixin.qq.com/cgi-bin/webhook/send?key="
```

Expected: no secret/runtime files tracked and no real WeCom Webhook key in tracked source.

---

## Self-Review Notes

- Spec coverage: initial manual learning, six-month window, 1000 total cap, INBOX + Sent only, Sent discovery, read-only access, system filtering, Message-ID dedupe, local SQLite, style profile, manual overrides, exact-customer history, safe company/domain fallback, incremental Sent learning, production failure isolation, multilingual behavior, draft-only safety, and real 163 verification are all mapped to explicit tasks.
- Deliberate V1 simplification: `customer_memory.recent_products_json`, `recent_topics_json`, and `last_thread_summary` are persisted but are not populated through a separate semantic-extraction LLM pass in V1. The reply path instead uses a bounded set of exact-customer historical messages, which avoids extra cost and reduces hallucination risk. These fields remain available for a later enhancement without changing the schema.
- No vector DB, fine-tuning, GUI, or cloud service is introduced.
- No task adds SMTP send capability.
