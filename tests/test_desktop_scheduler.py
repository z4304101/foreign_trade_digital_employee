from desktop.scheduler import DesktopScheduler


def test_scheduler_keeps_configured_poll_interval():
    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=lambda: {
            "total": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        },
        on_result=lambda result: None,
        on_error=lambda error: None,
    )

    assert scheduler.interval_seconds == 180
    assert scheduler.is_running is False
    assert scheduler.is_paused is False


def test_run_now_reuses_cycle_and_reports_result():
    calls = []
    results = []

    expected = {
        "total": 3,
        "processed": 1,
        "skipped": 2,
        "failed": 0,
    }

    def fake_cycle():
        calls.append("cycle")
        return expected

    def on_result(result):
        results.append(result)

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=fake_cycle,
        on_result=on_result,
        on_error=lambda error: None,
    )

    returned = scheduler.run_now()

    assert calls == ["cycle"]
    assert results == [expected]
    assert returned == expected


def test_run_now_reports_cycle_error_without_crashing_scheduler():
    errors = []

    expected_error = RuntimeError(
        "mail cycle failed"
    )

    def failing_cycle():
        raise expected_error

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=failing_cycle,
        on_result=lambda result: None,
        on_error=lambda error: errors.append(error),
    )

    returned = scheduler.run_now()

    assert returned is None
    assert errors == [expected_error]

    assert scheduler.is_running is False
    assert scheduler.is_paused is False


def test_start_uses_timer_and_tick_runs_same_cycle():
    calls = []
    results = []
    created_timers = []

    expected = {
        "total": 1,
        "processed": 1,
        "skipped": 0,
        "failed": 0,
    }

    class FakeTimer:
        def __init__(
            self,
            interval_seconds,
            callback,
        ):
            self.interval_seconds = interval_seconds
            self.callback = callback
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def fire(self):
            self.callback()

    def timer_factory(
        interval_seconds,
        callback,
    ):
        timer = FakeTimer(
            interval_seconds,
            callback,
        )
        created_timers.append(timer)
        return timer

    def fake_cycle():
        calls.append("cycle")
        return expected

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=fake_cycle,
        on_result=lambda result: results.append(result),
        on_error=lambda error: None,
        timer_factory=timer_factory,
    )

    scheduler.start()

    assert scheduler.is_running is True
    assert scheduler.is_paused is False

    assert len(created_timers) == 1

    timer = created_timers[0]

    assert timer.interval_seconds == 180
    assert timer.started is True

    # Simulate one automatic 180-second tick.
    timer.fire()

    assert calls == ["cycle"]
    assert results == [expected]


def test_pause_blocks_auto_tick_but_run_now_still_works_and_resume_restores_tick():
    calls = []
    created_timers = []

    class FakeTimer:
        def __init__(
            self,
            interval_seconds,
            callback,
        ):
            self.interval_seconds = interval_seconds
            self.callback = callback
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def fire(self):
            self.callback()

    def timer_factory(
        interval_seconds,
        callback,
    ):
        timer = FakeTimer(
            interval_seconds,
            callback,
        )
        created_timers.append(timer)
        return timer

    def fake_cycle():
        calls.append("cycle")
        return {
            "total": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        }

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=fake_cycle,
        on_result=lambda result: None,
        on_error=lambda error: None,
        timer_factory=timer_factory,
    )

    scheduler.start()

    timer = created_timers[0]

    assert scheduler.is_running is True
    assert scheduler.is_paused is False

    # Normal automatic tick works.
    timer.fire()

    assert calls == ["cycle"]

    scheduler.pause()

    assert scheduler.is_running is True
    assert scheduler.is_paused is True

    # Automatic tick must be ignored while paused.
    timer.fire()

    assert calls == ["cycle"]

    # Explicit user action is still allowed.
    scheduler.run_now()

    assert calls == [
        "cycle",
        "cycle",
    ]

    scheduler.resume()

    assert scheduler.is_running is True
    assert scheduler.is_paused is False

    # Automatic polling works again after resume.
    timer.fire()

    assert calls == [
        "cycle",
        "cycle",
        "cycle",
    ]


def test_stop_stops_timer_and_prevents_future_auto_ticks():
    calls = []
    created_timers = []

    class FakeTimer:
        def __init__(
            self,
            interval_seconds,
            callback,
        ):
            self.interval_seconds = interval_seconds
            self.callback = callback
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def fire(self):
            self.callback()

    def timer_factory(
        interval_seconds,
        callback,
    ):
        timer = FakeTimer(
            interval_seconds,
            callback,
        )
        created_timers.append(timer)
        return timer

    def fake_cycle():
        calls.append("cycle")
        return {
            "total": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        }

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=fake_cycle,
        on_result=lambda result: None,
        on_error=lambda error: None,
        timer_factory=timer_factory,
    )

    scheduler.start()

    timer = created_timers[0]

    timer.fire()

    assert calls == ["cycle"]

    scheduler.pause()

    assert scheduler.is_running is True
    assert scheduler.is_paused is True

    scheduler.stop()

    assert scheduler.is_running is False
    assert scheduler.is_paused is False
    assert timer.stopped is True

    # Even if an old timer callback somehow fires later,
    # stopped scheduler must not process mail.
    timer.fire()

    assert calls == ["cycle"]


def test_start_is_blocked_when_production_gate_is_not_ready():
    calls = []
    created_timers = []

    class FakeTimer:
        def __init__(
            self,
            interval_seconds,
            callback,
        ):
            self.callback = callback
            self.started = False

        def start(self):
            self.started = True

        def stop(self):
            pass

    def timer_factory(
        interval_seconds,
        callback,
    ):
        timer = FakeTimer(
            interval_seconds,
            callback,
        )
        created_timers.append(timer)
        return timer

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=lambda: calls.append("cycle"),
        on_result=lambda result: None,
        on_error=lambda error: None,
        timer_factory=timer_factory,
        ready_check=lambda: False,
    )

    started = scheduler.start()

    assert started is False
    assert scheduler.is_running is False
    assert scheduler.is_paused is False

    # Gate closed means timer must not even start.
    assert created_timers == []

    # Production cycle must never run.
    assert calls == []


def test_run_now_is_blocked_when_production_gate_is_not_ready():
    calls = []
    results = []
    errors = []

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=lambda: calls.append("cycle"),
        on_result=lambda result: results.append(result),
        on_error=lambda error: errors.append(error),
        ready_check=lambda: False,
    )

    returned = scheduler.run_now()

    assert returned is None

    # Manual check must not bypass onboarding/baseline gate.
    assert calls == []
    assert results == []
    assert errors == []

    assert scheduler.is_running is False
    assert scheduler.is_paused is False


def test_repeated_cycle_failures_update_health_tracker():
    from desktop.health import (
        AppStatus,
        HealthTracker,
        ServiceName,
    )

    tracker = HealthTracker()

    errors = []

    def failing_cycle():
        raise TimeoutError(
            "temporary network timeout"
        )

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=failing_cycle,
        on_result=lambda result: None,
        on_error=lambda error: errors.append(error),
        health_tracker=tracker,
        health_service=ServiceName.MAIL,
    )

    scheduler.run_now()
    scheduler.run_now()

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.RUNNING
    )

    scheduler.run_now()

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.NEEDS_ATTENTION
    )

    assert len(errors) == 3


def test_successful_cycle_resets_health_failure_count():
    from desktop.health import (
        AppStatus,
        HealthTracker,
        ServiceName,
    )

    tracker = HealthTracker()

    attempts = {
        "count": 0,
    }

    def flaky_cycle():
        attempts["count"] += 1

        if attempts["count"] <= 3:
            raise TimeoutError(
                "temporary network timeout"
            )

        return {
            "total": 1,
            "processed": 1,
            "skipped": 0,
            "failed": 0,
        }

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=flaky_cycle,
        on_result=lambda result: None,
        on_error=lambda error: None,
        health_tracker=tracker,
        health_service=ServiceName.MAIL,
    )

    scheduler.run_now()
    scheduler.run_now()
    scheduler.run_now()

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.NEEDS_ATTENTION
    )

    result = scheduler.run_now()

    assert result == {
        "total": 1,
        "processed": 1,
        "skipped": 0,
        "failed": 0,
    }

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.RUNNING
    )


def test_unrecoverable_cycle_error_immediately_marks_service_error():
    from desktop.health import (
        AppStatus,
        HealthTracker,
        ServiceName,
    )

    tracker = HealthTracker()
    errors = []

    expected_error = RuntimeError(
        "mail authentication expired"
    )

    def failing_cycle():
        raise expected_error

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=failing_cycle,
        on_result=lambda result: None,
        on_error=lambda error: errors.append(error),
        health_tracker=tracker,
        health_service=ServiceName.MAIL,
        unrecoverable_error_check=lambda error: True,
    )

    returned = scheduler.run_now()

    assert returned is None
    assert errors == [expected_error]

    assert (
        tracker.status(AppStatus.RUNNING)
        == AppStatus.SERVICE_ERROR
    )
