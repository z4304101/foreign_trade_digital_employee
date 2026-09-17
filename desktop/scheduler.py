from collections.abc import Callable
from typing import Any, Protocol

from desktop.health import (
    HealthTracker,
    ServiceName,
)


class CycleRunner(Protocol):
    """
    Optional execution adapter.

    Production Qt uses a QThreadPool-backed runner.
    Unit tests and non-GUI use may keep synchronous mode.
    """

    def submit(
        self,
        operation: Callable[
            [],
            dict[str, int],
        ],
        on_result: Callable[
            [dict[str, int]],
            None,
        ],
        on_error: Callable[
            [Exception],
            None,
        ],
    ) -> bool:
        ...


class DesktopScheduler:
    """
    Desktop polling scheduler.

    The scheduler itself remains Qt-independent.

    Without a runner:
        cycle executes synchronously, preserving
        existing unit-test/CLI behavior.

    With a runner:
        cycle is dispatched away from the GUI thread.

    Only one background cycle may be in flight.
    """

    def __init__(
        self,
        *,
        interval_seconds: int,
        cycle: Callable[
            [],
            dict[str, int],
        ],
        on_result: Callable[
            [dict[str, int]],
            None,
        ],
        on_error: Callable[
            [Exception],
            None,
        ],
        timer_factory: Callable[
            [int, Callable[[], None]],
            Any,
        ]
        | None = None,
        ready_check: Callable[
            [],
            bool,
        ]
        | None = None,
        health_tracker: HealthTracker
        | None = None,
        health_service: ServiceName
        | None = None,
        unrecoverable_error_check: Callable[
            [Exception],
            bool,
        ]
        | None = None,
        runner: CycleRunner
        | None = None,
    ) -> None:
        self.interval_seconds = (
            interval_seconds
        )

        self.cycle = cycle
        self.on_result = on_result
        self.on_error = on_error

        self.timer_factory = (
            timer_factory
        )

        self.ready_check = (
            ready_check
        )

        self.health_tracker = (
            health_tracker
        )

        self.health_service = (
            health_service
        )

        self.unrecoverable_error_check = (
            unrecoverable_error_check
        )

        self.runner = runner

        self._timer = None
        self._cycle_in_flight = False

        self.is_running = False
        self.is_paused = False

    @property
    def cycle_in_flight(
        self,
    ) -> bool:
        return self._cycle_in_flight

    def _record_failure(
        self,
        error: Exception,
    ) -> None:
        unrecoverable = False

        if (
            self.unrecoverable_error_check
            is not None
        ):
            unrecoverable = (
                self.unrecoverable_error_check(
                    error
                )
            )

        if (
            self.health_tracker
            is not None
            and self.health_service
            is not None
        ):
            self.health_tracker.record_failure(
                self.health_service,
                unrecoverable=(
                    unrecoverable
                ),
            )

        self.on_error(
            error
        )

    def _record_success(
        self,
        result: dict[str, int],
    ) -> None:
        if (
            self.health_tracker
            is not None
            and self.health_service
            is not None
        ):
            self.health_tracker.record_success(
                self.health_service
            )

        self.on_result(
            result
        )

    def _background_result(
        self,
        result: dict[str, int],
    ) -> None:
        self._cycle_in_flight = False

        self._record_success(
            result
        )

    def _background_error(
        self,
        error: Exception,
    ) -> None:
        self._cycle_in_flight = False

        self._record_failure(
            error
        )

    def run_now(
        self,
    ) -> dict[str, int] | None:
        """
        Run or dispatch one production cycle.

        Manual execution is allowed while paused,
        but it never bypasses the readiness gate.
        """

        if (
            self.ready_check
            is not None
            and not self.ready_check()
        ):
            return None

        #
        # Production GUI mode.
        #
        if self.runner is not None:
            if self._cycle_in_flight:
                return None

            self._cycle_in_flight = True

            try:
                accepted = (
                    self.runner.submit(
                        self.cycle,
                        self._background_result,
                        self._background_error,
                    )
                )

            except Exception as error:
                self._cycle_in_flight = False

                self._record_failure(
                    error
                )

                return None

            if accepted is False:
                self._cycle_in_flight = False

            return None

        #
        # Existing synchronous mode.
        #
        try:
            result = self.cycle()

        except Exception as error:
            self._record_failure(
                error
            )

            return None

        self._record_success(
            result
        )

        return result

    def _on_timer_tick(
        self,
    ) -> None:
        if not self.is_running:
            return

        if self.is_paused:
            return

        self.run_now()

    def start(
        self,
    ) -> bool:
        if self.is_running:
            return True

        if (
            self.ready_check
            is not None
            and not self.ready_check()
        ):
            return False

        if self.timer_factory is None:
            raise RuntimeError(
                "timer_factory is required "
                "to start scheduler"
            )

        self._timer = (
            self.timer_factory(
                self.interval_seconds,
                self._on_timer_tick,
            )
        )

        self.is_running = True
        self.is_paused = False

        self._timer.start()

        return True

    def pause(
        self,
    ) -> None:
        if not self.is_running:
            return

        self.is_paused = True

    def resume(
        self,
    ) -> None:
        if not self.is_running:
            return

        self.is_paused = False

    def stop(
        self,
    ) -> None:
        if self._timer is not None:
            self._timer.stop()

        self.is_running = False
        self.is_paused = False
        self._timer = None
