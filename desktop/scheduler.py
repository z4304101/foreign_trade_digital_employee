from collections.abc import Callable
from typing import Any


class DesktopScheduler:
    """
    Desktop background scheduler.

    Manual and automatic checks reuse the same cycle.

    Automatic timer ticks respect start / pause /
    resume / stop state.
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
    ) -> None:
        self.interval_seconds = interval_seconds

        self.cycle = cycle
        self.on_result = on_result
        self.on_error = on_error

        self.timer_factory = timer_factory
        self._timer = None

        self.is_running = False
        self.is_paused = False

    def run_now(
        self,
    ) -> dict[str, int] | None:
        """
        Run one mail-processing cycle immediately.

        Manual execution is allowed even while
        automatic polling is paused.
        """

        try:
            result = self.cycle()
        except Exception as error:
            self.on_error(
                error
            )
            return None

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
    ) -> None:
        """
        Start automatic polling.
        """

        if self.is_running:
            return

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

        Any stale timer callback that fires later
        is blocked by is_running=False.
        """

        if self._timer is not None:
            self._timer.stop()

        self.is_running = False
        self.is_paused = False
        self._timer = None
