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

    Production remains closed until the onboarding /
    baseline gate is ready.

    Normal settings may be opened from the dashboard,
    while advanced settings remain protected by their
    own administrator-authentication gate.
    """

    def __init__(
        self,
        *,
        dashboard_window: WindowLike,
        onboarding_window: WindowLike,
        scheduler: SchedulerLike,
        ready_check: Callable[
            [],
            bool,
        ],
        settings_window: WindowLike | None = None,
    ) -> None:
        self.dashboard_window = (
            dashboard_window
        )

        self.onboarding_window = (
            onboarding_window
        )

        self.settings_window = (
            settings_window
        )

        self.scheduler = scheduler

        self.ready_check = (
            ready_check
        )

        self._scheduler_started = False

    def _start_scheduler_once(
        self,
    ) -> None:
        if self._scheduler_started:
            return

        started = (
            self.scheduler.start()
        )

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
        if not self.ready_check():
            return

        self.onboarding_window.hide()

        self.dashboard_window.show()

        self._start_scheduler_once()

    def open_settings(
        self,
    ) -> None:
        if self.settings_window is None:
            return

        self.settings_window.show()

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
