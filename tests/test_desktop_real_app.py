import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from desktop.credentials import (
    MemoryCredentialStore,
)
from desktop.paths import DesktopPaths


class FakeRunner:
    def submit(
        self,
        operation,
        on_result,
        on_error,
    ):
        return True


class FakeAutostart:
    def __init__(self):
        self.enabled = False

    def enable(
        self,
        command,
    ):
        self.enabled = True

    def disable(
        self,
    ):
        self.enabled = False

    def is_enabled(
        self,
    ):
        return self.enabled


def test_create_application_builds_real_desktop_stack_without_network(
    tmp_path,
):
    from desktop.app import (
        create_application,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    paths = DesktopPaths.from_root(
        tmp_path
    )

    credentials = (
        MemoryCredentialStore()
    )

    runner = FakeRunner()

    desktop = create_application(
        paths=paths,
        credentials=credentials,
        qapp=app,
        runner=runner,
        autostart_adapter=FakeAutostart(),
        enable_tray=False,
    )

    assert desktop.paths == paths

    assert (
        desktop.credentials
        is credentials
    )

    assert (
        desktop.configuration.credentials
        is credentials
    )

    assert (
        desktop.setup_controller.configuration
        is desktop.configuration
    )

    assert (
        desktop.scheduler.runner
        is runner
    )

    #
    # Fresh install must remain behind
    # onboarding/baseline gate.
    #
    assert (
        desktop.ready_check()
        is False
    )

    desktop.show()

    assert (
        desktop.onboarding_window.isVisible()
        is True
    )

    assert (
        desktop.dashboard_window.isVisible()
        is False
    )

    assert (
        desktop.scheduler.is_running
        is False
    )

    desktop.onboarding_window.hide()
    desktop.dashboard_window.hide()


def test_create_application_uses_user_data_not_repository_for_runtime(
    tmp_path,
):
    from desktop.app import (
        create_application,
    )

    app = (
        QApplication.instance()
        or QApplication([])
    )

    paths = DesktopPaths.from_root(
        tmp_path
        / "user-data"
    )

    desktop = create_application(
        paths=paths,
        credentials=MemoryCredentialStore(),
        qapp=app,
        runner=FakeRunner(),
        autostart_adapter=FakeAutostart(),
        enable_tray=False,
    )

    assert (
        desktop.configuration.settings_store.path
        == paths.settings_file
    )

    assert paths.root.exists()

    assert paths.result_dir.exists()
    assert paths.log_dir.exists()
    assert paths.backup_dir.exists()


def test_run_desktop_entrypoint_exposes_real_main():
    import run_desktop

    assert callable(
        run_desktop.main
    )
