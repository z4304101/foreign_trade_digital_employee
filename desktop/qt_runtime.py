from collections.abc import Callable

from PySide6.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    Qt,
    Signal,
    Slot,
)


class QtTimerHandle:
    """
    QTimer wrapper expected by DesktopScheduler.

    DesktopScheduler speaks seconds.
    Qt speaks milliseconds.
    """

    def __init__(
        self,
        interval_seconds: int,
        callback: Callable[
            [],
            None,
        ],
        parent: QObject | None = None,
    ) -> None:
        self.timer = QTimer(
            parent
        )

        self.timer.setInterval(
            int(
                interval_seconds
                * 1000
            )
        )

        self.timer.timeout.connect(
            callback
        )

    def start(
        self,
    ) -> None:
        self.timer.start()

    def stop(
        self,
    ) -> None:
        self.timer.stop()


def qt_timer_factory(
    interval_seconds: int,
    callback: Callable[
        [],
        None,
    ],
):
    return QtTimerHandle(
        interval_seconds,
        callback,
    )


class _WorkerSignals(QObject):
    result = Signal(
        object
    )

    error = Signal(
        object
    )

    finished = Signal(
        object
    )


class _CycleRunnable(QRunnable):
    def __init__(
        self,
        operation: Callable[
            [],
            object,
        ],
    ) -> None:
        super().__init__()

        self.operation = (
            operation
        )

        self.signals = (
            _WorkerSignals()
        )

    @Slot()
    def run(
        self,
    ) -> None:
        try:
            result = (
                self.operation()
            )

        except Exception as error:
            self.signals.error.emit(
                error
            )

        else:
            self.signals.result.emit(
                result
            )

        finally:
            self.signals.finished.emit(
                self
            )


class QtThreadPoolRunner(QObject):
    """
    Executes IMAP/LLM work in QThreadPool.

    Completion signals are queued back to the
    QObject's GUI thread.
    """

    def __init__(
        self,
        *,
        pool: QThreadPool
        | None = None,
        parent: QObject
        | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.pool = (
            pool
            or QThreadPool.globalInstance()
        )

        self._tasks = []

    def submit(
        self,
        operation,
        on_result,
        on_error,
    ) -> bool:
        task = _CycleRunnable(
            operation
        )

        self._tasks.append(
            task
        )

        task.signals.result.connect(
            on_result,
            Qt.ConnectionType.QueuedConnection,
        )

        task.signals.error.connect(
            on_error,
            Qt.ConnectionType.QueuedConnection,
        )

        task.signals.finished.connect(
            self._cleanup,
            Qt.ConnectionType.QueuedConnection,
        )

        self.pool.start(
            task
        )

        return True

    @Slot(object)
    def _cleanup(
        self,
        task,
    ) -> None:
        try:
            self._tasks.remove(
                task
            )
        except ValueError:
            pass
