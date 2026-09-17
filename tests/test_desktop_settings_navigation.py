from desktop.app import (
    DesktopApplication,
)


class FakeWindow:
    def __init__(self):
        self.show_calls = 0
        self.hide_calls = 0

    def show(self):
        self.show_calls += 1

    def hide(self):
        self.hide_calls += 1


class FakeScheduler:
    def start(self):
        return True

    def pause(self):
        pass

    def resume(self):
        pass

    def run_now(self):
        return None


def test_desktop_application_opens_settings_window():
    dashboard = FakeWindow()
    onboarding = FakeWindow()
    settings = FakeWindow()

    desktop = DesktopApplication(
        dashboard_window=dashboard,
        onboarding_window=onboarding,
        settings_window=settings,
        scheduler=FakeScheduler(),
        ready_check=lambda: True,
    )

    desktop.open_settings()

    assert settings.show_calls == 1
