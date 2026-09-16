from desktop.health import (
    AppStatus,
    HealthTracker,
    ServiceName,
)


def test_health_tracker_escalates_after_repeated_failures():
    tracker = HealthTracker()

    tracker.record_failure(
        ServiceName.MAIL
    )
    tracker.record_failure(
        ServiceName.MAIL
    )

    assert (
        tracker.status(
            AppStatus.RUNNING
        )
        == AppStatus.RUNNING
    )

    tracker.record_failure(
        ServiceName.MAIL
    )

    assert (
        tracker.status(
            AppStatus.RUNNING
        )
        == AppStatus.NEEDS_ATTENTION
    )

    tracker.record_failure(
        ServiceName.MAIL
    )

    assert (
        tracker.status(
            AppStatus.RUNNING
        )
        == AppStatus.NEEDS_ATTENTION
    )

    tracker.record_failure(
        ServiceName.MAIL
    )

    assert (
        tracker.status(
            AppStatus.RUNNING
        )
        == AppStatus.SERVICE_ERROR
    )

    tracker.record_success(
        ServiceName.MAIL
    )

    assert (
        tracker.status(
            AppStatus.RUNNING
        )
        == AppStatus.RUNNING
    )


def test_unrecoverable_failure_immediately_becomes_service_error():
    tracker = HealthTracker()

    tracker.record_failure(
        ServiceName.AI,
        unrecoverable=True,
    )

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.SERVICE_ERROR
    )


def test_service_failure_counts_are_independent():
    tracker = HealthTracker()

    for _ in range(3):
        tracker.record_failure(
            ServiceName.MAIL
        )

    tracker.record_failure(
        ServiceName.WECOM
    )

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.NEEDS_ATTENTION
    )

    tracker.record_success(
        ServiceName.WECOM
    )

    # WeCom recovery must NOT erase
    # the existing MAIL failures.
    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.NEEDS_ATTENTION
    )

    tracker.record_success(
        ServiceName.MAIL
    )

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.RUNNING
    )


def test_dashboard_snapshot_contains_only_status_summary():
    from desktop.models import (
        DashboardSnapshot,
        ProcessRecord,
    )

    record = ProcessRecord(
        sender="customer@example.com",
        subject="RFQ for Model A",
        processed_at="2026-09-16 12:30",
        analysis_completed=True,
        draft_saved=True,
        wecom_notified=True,
    )

    snapshot = DashboardSnapshot(
        status=AppStatus.RUNNING,
        last_check_at="12:30",
        next_check_at="12:33",
        today_scanned=10,
        today_new_inquiries=2,
        today_drafts=2,
        history_ready=True,
        style_ready=True,
        wecom_connected=True,
        recent_records=(record,),
    )

    assert snapshot.status == AppStatus.RUNNING
    assert snapshot.today_scanned == 10
    assert snapshot.today_new_inquiries == 2
    assert snapshot.today_drafts == 2
    assert len(snapshot.recent_records) == 1

    saved = snapshot.recent_records[0]

    assert saved.sender == "customer@example.com"
    assert saved.subject == "RFQ for Model A"
    assert saved.analysis_completed is True
    assert saved.draft_saved is True
    assert saved.wecom_notified is True

    # Desktop summary records intentionally have
    # no field for storing the full customer body.
    assert not hasattr(
        saved,
        "body",
    )
