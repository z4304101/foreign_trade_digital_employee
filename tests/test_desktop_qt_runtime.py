import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from desktop.scheduler import DesktopScheduler


def test_scheduler_dispatches_cycle_without_blocking_and_blocks_overlap():
    calls = []
    results = []
    pending = []

    expected = {
        "total": 1,
        "processed": 1,
        "skipped": 0,
        "failed": 0,
    }

    class FakeRunner:
        def submit(
            self,
            operation,
            on_result,
            on_error,
        ):
            pending.append(
                (
                    operation,
                    on_result,
                    on_error,
                )
            )
            return True

    def cycle():
        calls.append(
            "cycle"
        )
        return expected

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=cycle,
        on_result=lambda result: (
            results.append(result)
        ),
        on_error=lambda error: None,
        runner=FakeRunner(),
    )

    returned = scheduler.run_now()

    assert returned is None

    #
    # The network/AI cycle must NOT have run
    # on the caller / GUI thread.
    #
    assert calls == []
    assert len(pending) == 1

    #
    # While one cycle is in flight, another
    # click/timer tick must not start a second one.
    #
    scheduler.run_now()

    assert len(pending) == 1

    (
        operation,
        on_result,
        on_error,
    ) = pending.pop()

    result = operation()

    on_result(
        result
    )

    assert calls == [
        "cycle",
    ]

    assert results == [
        expected,
    ]

    #
    # Completion releases the in-flight gate.
    #
    scheduler.run_now()

    assert len(pending) == 1


def test_background_error_releases_inflight_gate_and_reports_error():
    errors = []
    pending = []

    class FakeRunner:
        def submit(
            self,
            operation,
            on_result,
            on_error,
        ):
            pending.append(
                (
                    operation,
                    on_result,
                    on_error,
                )
            )
            return True

    scheduler = DesktopScheduler(
        interval_seconds=180,
        cycle=lambda: {
            "total": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        },
        on_result=lambda result: None,
        on_error=lambda error: (
            errors.append(error)
        ),
        runner=FakeRunner(),
    )

    scheduler.run_now()

    assert len(pending) == 1

    (
        operation,
        on_result,
        on_error,
    ) = pending.pop()

    expected = RuntimeError(
        "background failure"
    )

    on_error(
        expected
    )

    assert errors == [
        expected,
    ]

    #
    # Error must not leave the scheduler
    # permanently locked.
    #
    scheduler.run_now()

    assert len(pending) == 1


def test_qt_timer_converts_seconds_to_milliseconds():
    from desktop.qt_runtime import (
        QtTimerHandle,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    timer = QtTimerHandle(
        180,
        lambda: None,
    )

    assert (
        timer.timer.interval()
        == 180000
    )

    timer.start()

    assert (
        timer.timer.isActive()
        is True
    )

    timer.stop()

    assert (
        timer.timer.isActive()
        is False
    )
