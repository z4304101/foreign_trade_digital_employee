from desktop.credentials import (
    AI_API_KEY,
    EMAIL_AUTH_CODE,
    WECOM_WEBHOOK,
    MemoryCredentialStore,
)


def test_memory_credential_store_round_trip():
    store = MemoryCredentialStore()

    store.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )

    store.set(
        AI_API_KEY,
        "ai-secret",
    )

    store.set(
        WECOM_WEBHOOK,
        "https://example.invalid/hook",
    )

    assert (
        store.get(EMAIL_AUTH_CODE)
        == "mail-secret"
    )

    assert (
        store.get(AI_API_KEY)
        == "ai-secret"
    )

    assert (
        store.get(WECOM_WEBHOOK)
        == "https://example.invalid/hook"
    )


def test_memory_credential_store_delete():
    store = MemoryCredentialStore()

    store.set(
        EMAIL_AUTH_CODE,
        "mail-secret",
    )

    store.delete(
        EMAIL_AUTH_CODE
    )

    assert (
        store.get(EMAIL_AUTH_CODE)
        is None
    )
