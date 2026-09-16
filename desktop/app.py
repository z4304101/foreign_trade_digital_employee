from collections.abc import Callable
from typing import Protocol


class WindowLike(Protocol):
    def show(self) -> None:
        ...


class SchedulerLike(Protocol):
    def start(self):
        ...


class DesktopApplication:
    """
    Top-level desktop application controller.

    Production processing must remain closed until
    onboarding/baseline safety checks are complete.
    """

    def __init__(
        self,
        *,
        window: WindowLike,
        scheduler: SchedulerLike,
        ready_check: Callable[[], bool],
    ) -> None:
        self.window = window
        self.scheduler = scheduler
        self.ready_check = ready_check

    def show(self) -> None:
        self.window.show()

        if self.ready_check():
            self.scheduler.start()

    def pause(self) -> None:
        self.scheduler.pause()

    def resume(self) -> None:
        self.scheduler.resume()

    def run_now(self):
        return self.scheduler.run_now()
