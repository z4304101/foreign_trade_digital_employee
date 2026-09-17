import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication


def test_dashboard_close_hides_instead_of_quitting_when_tray_mode_enabled():
    from desktop.ui.dashboard_window import (
        DashboardWindow,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    class FakeEvent:
        def __init__(self):
            self.ignored = False

        def ignore(self):
            self.ignored = True

    window = DashboardWindow()

    window.set_close_to_tray(
        True
    )

    window.show()

    event = FakeEvent()

    window.closeEvent(
        event
    )

    assert event.ignored is True

    assert (
        window.isVisible()
        is False
    )


def test_tray_controls_same_scheduler_and_explicit_quit_stops_it():
    from desktop.ui.tray import (
        TrayController,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    calls = []

    class FakeWindow:
        def show(self):
            calls.append(
                "show"
            )

        def raise_(self):
            calls.append(
                "raise"
            )

        def activateWindow(self):
            calls.append(
                "activate"
            )

    class FakeScheduler:
        def __init__(self):
            self.is_paused = False

        def pause(self):
            self.is_paused = True
            calls.append(
                "pause"
            )

        def resume(self):
            self.is_paused = False
            calls.append(
                "resume"
            )

        def run_now(self):
            calls.append(
                "run_now"
            )

        def stop(self):
            calls.append(
                "stop"
            )

    scheduler = FakeScheduler()

    controller = TrayController(
        window=FakeWindow(),
        scheduler=scheduler,
        on_settings=lambda: (
            calls.append(
                "settings"
            )
        ),
        on_quit=lambda: (
            calls.append(
                "quit"
            )
        ),
    )

    controller.open_window()

    assert calls[:3] == [
        "show",
        "raise",
        "activate",
    ]

    controller.toggle_pause()

    assert (
        scheduler.is_paused
        is True
    )

    assert (
        controller.pause_action.text()
        == "继续工作"
    )

    controller.toggle_pause()

    assert (
        scheduler.is_paused
        is False
    )

    controller.run_now()

    controller.open_settings()

    controller.quit_application()

    assert "pause" in calls
    assert "resume" in calls
    assert "run_now" in calls
    assert "settings" in calls

    assert calls[-2:] == [
        "stop",
        "quit",
    ]
