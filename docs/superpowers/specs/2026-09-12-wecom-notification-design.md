# WeCom Notification Design

## Goal

Add an optional WeCom notification channel to the Foreign Trade
Digital Employee.

When a customer email is successfully analyzed and its reply draft
has been saved to the email Drafts folder, the system can send an
internal notification to a WeCom group robot.

The existing email workflow must remain unchanged.

---

## Core Principle

Email remains the primary workflow.

WeCom is only an internal notification channel.

The system must continue to:

1. Read customer emails.
2. Filter non-customer messages.
3. Run AI analysis.
4. Generate a reply draft.
5. Apply the configured sender signature.
6. Save the reply to the email Drafts folder.
7. Record the processed Message-ID.

The system must NEVER automatically send an email to the customer.

---

## Workflow

Customer email
    |
    v
Customer email filter
    |
    v
AI analysis
    |
    v
Generate reply
    |
    v
Apply sender signature
    |
    v
Save reply to Drafts
    |
    v
Mark Message-ID as processed
    |
    +----------------------+
    |                      |
    v                      v
Email workflow done    WeCom notification
                           |
                           v
                    Internal employee group

---

## WeCom Phase 1

Phase 1 uses a WeCom group robot Webhook.

The robot is only responsible for sending internal notifications.

It does not:

- send customer emails
- modify customer emails
- approve replies
- communicate directly with external customers
- provide interactive chat commands

Interactive WeCom bot support will be implemented in a later phase.

---

## Notification Content

Initial notification:

📩 New customer inquiry

From: customer email sender

Subject: customer email subject

✅ AI analysis completed
✅ Reply draft saved to mailbox
✅ Customer email was not automatically sent

The first version intentionally keeps the notification simple.

More structured information such as customer name, company,
product, quantity, risk level and quotation details can be added
later.

---

## Configuration

The WeCom Webhook URL must never be hardcoded.

Temporary configuration:

WECOM_WEBHOOK_URL

The value will be stored locally and must never be committed to Git.

If WECOM_WEBHOOK_URL is empty or missing:

- the WeCom notification feature is disabled
- email processing continues normally

Future desktop versions will hide this configuration behind the
Windows/macOS setup interface.

---

## Project Structure

New package:

wecom/

Files:

wecom/__init__.py

wecom/config.py
- Load WeCom configuration.
- Webhook is optional.

wecom/notifier.py
- Build WeCom notification content.
- Send text messages through the Webhook.
- Never send customer email.

Tests:

tests/test_wecom_config.py

tests/test_wecom_notifier.py

tests/test_wecom_integration.py

---

## Integration Point

The WeCom notification must only be attempted after:

1. The reply draft has been successfully saved.
2. The Message-ID has been successfully recorded as processed.

Then:

notify WeCom

This prevents a failed WeCom notification from causing duplicate
customer email drafts.

---

## Failure Rules

WeCom is a secondary channel.

Therefore:

If the email draft fails:
- normal email processing failure rules apply
- do not send a WeCom success notification

If WeCom notification fails:
- do not delete the email draft
- do not retry the customer email
- do not remove the processed Message-ID
- do not increment the email batch failed count
- continue processing later emails

A WeCom outage must never break the email workflow.

---

## Security

WECOM_WEBHOOK_URL is treated as a secret.

It must never:

- appear in source code
- appear in GitHub
- appear in logs
- appear in test fixtures as a real Webhook
- be printed to the terminal

Tests use fake URLs only.

---

## Testing Strategy

Development follows TDD.

Required tests:

1. Missing Webhook disables notification safely.
2. Notification payload contains expected text.
3. Successful WeCom response is accepted.
4. WeCom API failure is handled safely.
5. Network failure is handled safely.
6. WeCom failure does not fail email processing.
7. Existing email draft behavior remains unchanged.
8. Existing full regression suite must remain green.

---

## Phase 1 Acceptance Criteria

Phase 1 is complete when:

- a real customer email creates an email draft
- the email is never automatically sent
- the Message-ID is recorded
- a WeCom group receives the internal notification
- disabling WeCom does not affect email processing
- breaking the WeCom connection does not affect email processing
- all automated tests pass

---

## Non-Goals

The following are intentionally excluded from Phase 1:

- WeCom interactive commands
- WeCom long-connection bot
- direct customer messaging
- automatic customer email sending
- CRM integration
- multi-user permissions
- desktop GUI
- Windows installer
- macOS installer

These will be implemented in later phases.