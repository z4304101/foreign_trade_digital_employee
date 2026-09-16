from collections.abc import Callable
from typing import Any

from desktop.health import (
    HealthTracker,
    ServiceName,
)


class DesktopScheduler:
    """
    Desktop background scheduler.

    Manual and automatic checks reuse the same cycle.

    Automatic polling can only start when the optional
    production readiness gate allows it.

    Ordinary cycle failures can also be reported to the
    desktop health tracker.
    """

    def __init__(
        self,
        *,
        interval_seconds: int,
        cycle: Callable[[], dict[str, int]],
        on_result: Callable[[dict[str, int]], None],
        on_error: Callable[[Exception], None],
        timer_factory: Callable[
            [int, Callable[[], None]],
            Any,
        ]
        | None = None,
        ready_check: Callable[[], bool] | None = None,
        health_tracker: HealthTracker | None = None,
        health_service: ServiceName | None = None,
        unrecoverable_error_check: Callable[[Exception], bool] | None = None,
    ) -> None:
        self.interval_seconds = interval_seconds

        self.cycle = cycle
        self.on_result = on_result
        self.on_error = on_error

        self.timer_factory = timer_factory
        self.ready_check = ready_check

        self.health_tracker = health_tracker
        self.health_service = health_service
        self.unrecoverable_error_check = unrecoverable_error_check

        self._timer = None

        self.is_running = False
        self.is_paused = False

    def run_now(
        self,
    ) -> dict[str, int] | None:
        """
        Run one mail-processing cycle immediately.

        Manual execution is allowed while paused, but it
        must never bypass the production readiness gate.
        """

        if (
            self.ready_check is not None
            and not self.ready_check()
        ):
            return None

        try:
            result = self.cycle()

        except Exception as error:
            unrecoverable = False

            if self.unrecoverable_error_check is not None:
                unrecoverable = self.unrecoverable_error_check(
                    error
                )

            if (
                self.health_tracker is not None
                and self.health_service is not None
            ):
                self.health_tracker.record_failure(
                    self.health_service,
                    unrecoverable=unrecoverable,
                )

            self.on_error(
                error
            )

            return None

        if (
            self.health_tracker is not None
            and self.health_service is not None
        ):
            self.health_tracker.record_success(
                self.health_service
            )

        self.on_result(
            result
        )

        return result

    def _on_timer_tick(
        self,
    ) -> None:
        """
        Handle one automatic polling tick.
        """

        if not self.is_running:
            return

        if self.is_paused:
            return

        self.run_now()

    def start(
        self,
    ) -> bool:
        """
        Start automatic polling.

        Returns False when the production readiness
        gate is closed. In that case no timer is created.
        """

        if self.is_running:
            return True

        if (
            self.ready_check is not None
            and not self.ready_check()
        ):
            return False

        if self.timer_factory is None:
            raise RuntimeError(
                "timer_factory is required to start scheduler"
            )

        self._timer = self.timer_factory(
            self.interval_seconds,
            self._on_timer_tick,
        )

        self.is_running = True
        self.is_paused = False

        self._timer.start()

        return True

    def pause(
        self,
    ) -> None:
        """
        Pause automatic polling.

        Manual run_now() remains available.
        """

        if not self.is_running:
            return

        self.is_paused = True

    def resume(
        self,
    ) -> None:
        """
        Resume automatic polling.
        """

        if not self.is_running:
            return

        self.is_paused = False

    def stop(
        self,
    ) -> None:
        """
        Stop automatic polling completely.
        """

        if self._timer is not None:
            self._timer.stop()

        self.is_running = False
        self.is_paused = False
        self._timer = None
