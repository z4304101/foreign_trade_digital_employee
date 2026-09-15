from types import SimpleNamespace

import pytest

from history_learning.store import HistoryStore


def test_run_batch_forwards_history_loader_when_supplied(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    mail = SimpleNamespace(
        message_id="<customer@example.com>",
        sender="Pierre <pierre@example.com>",
        subject="RFQ",
    )

    monkeypatch.setattr(
        runner,
        "read_recent_emails",
        lambda config, limit=20: [mail],
    )

    monkeypatch.setattr(
        runner,
        "is_customer_email_candidate",
        lambda input_mail: True,
    )

    fake_loader = object()

    captured = {}

    def fake_process_mail(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return "RESULT"

    monkeypatch.setattr(
        runner,
        "process_mail",
        fake_process_mail,
    )

    summary = runner.run_batch(
        provider=object(),
        mail_config=object(),
        skill_path=tmp_path / "SKILL.md",
        result_path=tmp_path / "latest.md",
        processed_store_path=(
            tmp_path / "processed.txt"
        ),
        create_draft=True,
        history_context_loader=fake_loader,
    )

    assert summary == {
        "total": 1,
        "processed": 1,
        "skipped": 0,
        "failed": 0,
    }

    assert (
        captured[
            "history_context_loader"
        ]
        is fake_loader
    )


def test_batch_main_uses_initialized_history_even_if_incremental_sync_fails(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    db_path = (
        tmp_path
        / "history_learning.db"
    )

    store = HistoryStore(
        db_path
    )
    store.initialize()

    store.set_learning_state(
        {
            "initial_learning_completed": "true",
            "last_sent_sync_at": (
                "2026-09-14T12:00:00+00:00"
            ),
        }
    )

    monkeypatch.setattr(
        runner,
        "HISTORY_DB_PATH",
        db_path,
        raising=False,
    )

    fake_mail_config = SimpleNamespace(
        email_user="sales@example.com",
    )

    fake_llm_config = object()
    fake_provider = object()

    monkeypatch.setattr(
        runner,
        "load_mail_config",
        lambda: fake_mail_config,
    )

    monkeypatch.setattr(
        runner,
        "load_llm_config",
        lambda: fake_llm_config,
    )

    monkeypatch.setattr(
        runner,
        "create_llm_provider",
        lambda config: fake_provider,
    )

    sync_calls = []

    def fake_sync_sent_incremental(
        mail_config,
        provider,
        store,
    ):
        sync_calls.append(
            True
        )

        raise RuntimeError(
            "temporary history sync failure"
        )

    monkeypatch.setattr(
        runner,
        "sync_sent_incremental",
        fake_sync_sent_incremental,
        raising=False,
    )

    fake_loader = object()

    monkeypatch.setattr(
        runner,
        "HistoryContextLoader",
        lambda store: fake_loader,
        raising=False,
    )

    captured = {}

    def fake_run_batch(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return {
            "total": 2,
            "processed": 1,
            "skipped": 1,
            "failed": 0,
        }

    monkeypatch.setattr(
        runner,
        "run_batch",
        fake_run_batch,
    )

    summary = runner.batch_main()

    assert summary == {
        "total": 2,
        "processed": 1,
        "skipped": 1,
        "failed": 0,
    }

    # Incremental learning was attempted.
    assert sync_calls == [
        True
    ]

    # Even though incremental learning failed,
    # normal customer processing still runs
    # with previously stored history.
    assert (
        captured[
            "history_context_loader"
        ]
        is fake_loader
    )


def test_batch_main_does_not_auto_learn_before_initial_learning(
    tmp_path,
    monkeypatch,
):
    import run_foreign_trade_agent as runner

    db_path = (
        tmp_path
        / "history_learning.db"
    )

    store = HistoryStore(
        db_path
    )
    store.initialize()

    # Deliberately do NOT set:
    #
    # initial_learning_completed=true

    monkeypatch.setattr(
        runner,
        "HISTORY_DB_PATH",
        db_path,
        raising=False,
    )

    monkeypatch.setattr(
        runner,
        "load_mail_config",
        lambda: SimpleNamespace(
            email_user="sales@example.com",
        ),
    )

    monkeypatch.setattr(
        runner,
        "load_llm_config",
        lambda: object(),
    )

    monkeypatch.setattr(
        runner,
        "create_llm_provider",
        lambda config: object(),
    )

    def forbidden_sync(
        *args,
        **kwargs,
    ):
        raise AssertionError(
            "incremental sync must not run "
            "before manual initial learning"
        )

    monkeypatch.setattr(
        runner,
        "sync_sent_incremental",
        forbidden_sync,
        raising=False,
    )

    captured = {}

    def fake_run_batch(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return {
            "total": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        }

    monkeypatch.setattr(
        runner,
        "run_batch",
        fake_run_batch,
    )

    summary = runner.batch_main()

    assert summary["failed"] == 0

    assert (
        "history_context_loader"
        not in captured
    )


def test_manual_learn_history_entry_point_runs_initial_learning(
    tmp_path,
    monkeypatch,
):
    try:
        import learn_history
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"learn_history.py is missing: {exc}"
        )

    fake_mail_config = object()
    fake_llm_config = object()
    fake_provider = object()

    monkeypatch.setattr(
        learn_history,
        "load_mail_config",
        lambda: fake_mail_config,
    )

    monkeypatch.setattr(
        learn_history,
        "load_llm_config",
        lambda: fake_llm_config,
    )

    monkeypatch.setattr(
        learn_history,
        "create_llm_provider",
        lambda config: fake_provider,
    )

    db_path = (
        tmp_path
        / "history_learning.db"
    )

    monkeypatch.setattr(
        learn_history,
        "HISTORY_DB_PATH",
        db_path,
    )

    captured = {}

    expected_summary = SimpleNamespace(
        scanned=100,
        learned=80,
        skipped=15,
        failed=5,
        sent_mailbox_found=True,
        style_profile_updated=True,
        warning="",
    )

    def fake_run_initial_learning(
        mail_config,
        provider,
        db_path,
    ):
        captured[
            "mail_config"
        ] = mail_config

        captured[
            "provider"
        ] = provider

        captured[
            "db_path"
        ] = db_path

        return expected_summary

    monkeypatch.setattr(
        learn_history,
        "run_initial_learning",
        fake_run_initial_learning,
    )

    result = learn_history.main()

    assert result is expected_summary

    assert (
        captured["mail_config"]
        is fake_mail_config
    )

    assert (
        captured["provider"]
        is fake_provider
    )

    assert (
        captured["db_path"]
        == db_path
    )
