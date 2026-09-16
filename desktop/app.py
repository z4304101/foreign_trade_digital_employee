from collections.abc import Callable
from typing import Protocol


class WindowLike(Protocol):
    def show(self) -> None:
        ...

    def hide(self) -> None:
        ...


class SchedulerLike(Protocol):
    def start(self):
        ...

    def pause(self) -> None:
        ...

    def resume(self) -> None:
        ...

    def run_now(self):
        ...


class DesktopApplication:
    """
    Top-level desktop application controller.

    Before the onboarding / baseline production gate
    is ready, only the onboarding window may be shown.

    After the gate is ready, the dashboard is shown and
    the scheduler is started at most once.
    """

    def __init__(
        self,
        *,
        dashboard_window: WindowLike,
        onboarding_window: WindowLike,
        scheduler: SchedulerLike,
        ready_check: Callable[[], bool],
    ) -> None:
        self.dashboard_window = dashboard_window
        self.onboarding_window = onboarding_window
        self.scheduler = scheduler
        self.ready_check = ready_check

        self._scheduler_started = False

    def _start_scheduler_once(
        self,
    ) -> None:
        if self._scheduler_started:
            return

        started = self.scheduler.start()

        if started:
            self._scheduler_started = True

    def show(
        self,
    ) -> None:
        if self.ready_check():
            self.dashboard_window.show()
            self._start_scheduler_once()
            return

        self.onboarding_window.show()

    def on_onboarding_complete(
        self,
    ) -> None:
        #
        # Never open production mode merely because the
        # user clicked a UI button. The safety gate must
        # actually be ready.
        #
        if not self.ready_check():
            return

        self.onboarding_window.hide()
        self.dashboard_window.show()
        self._start_scheduler_once()

    def pause(
        self,
    ) -> None:
        self.scheduler.pause()

    def resume(
        self,
    ) -> None:
        self.scheduler.resume()

    def run_now(
        self,
    ):
        return self.scheduler.run_now()
