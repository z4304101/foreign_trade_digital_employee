import shlex
import sys

from copy import deepcopy
from pathlib import Path
from collections.abc import Callable
from typing import Protocol

from PySide6.QtCore import (
    QEventLoop,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
)

from desktop.autostart import (
    create_autostart_adapter,
)
from desktop.configuration import (
    DesktopConfiguration,
)
from desktop.core_bridge import (
    DesktopCoreBridge,
)
from desktop.credentials import (
    KeyringCredentialStore,
)
from desktop.health import (
    AppStatus,
    HealthTracker,
    ServiceName,
)
from desktop.models import (
    DashboardSnapshot,
)
from desktop.onboarding import (
    OnboardingService,
)
from desktop.paths import (
    DesktopPaths,
)
from desktop.qt_runtime import (
    QtThreadPoolRunner,
    qt_timer_factory,
)
from desktop.scheduler import (
    DesktopScheduler,
)
from desktop.settings_store import (
    SettingsStore,
)
from desktop.setup_controller import (
    DesktopSetupController,
)
from desktop.ui.admin_unlock_dialog import (
    AdminUnlockDialog,
)
from desktop.ui.advanced_settings_dialog import (
    AdvancedSettingsDialog,
)
from desktop.ui.dashboard_window import (
    DashboardWindow,
)
from desktop.ui.onboarding_window import (
    OnboardingWindow,
)
from desktop.ui.settings_dialog import (
    SettingsDialog,
)
from desktop.ui.theme import (
    apply_light_theme,
)
from desktop.ui.tray import (
    TrayController,
)


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


class _CallbackWindow:
    """
    Window-like adapter used for settings.

    Each open rebuilds the dialog from the newest
    persisted configuration.
    """

    def __init__(
        self,
        opener: Callable[
            [],
            None,
        ],
    ) -> None:
        self.opener = opener

    def show(
        self,
    ) -> None:
        self.opener()

    def hide(
        self,
    ) -> None:
        pass


class _PrimaryWindowRouter:
    """
    Tray opens onboarding until the safe production
    gate is ready. Once ready, it opens Dashboard.
    """

    def __init__(
        self,
        *,
        dashboard,
        onboarding,
        ready_check,
    ) -> None:
        self.dashboard = dashboard
        self.onboarding = onboarding
        self.ready_check = (
            ready_check
        )

    def _target(
        self,
    ):
        if self.ready_check():
            return self.dashboard

        return self.onboarding

    def show(
        self,
    ) -> None:
        self._target().show()

    def raise_(
        self,
    ) -> None:
        target = self._target()

        if hasattr(
            target,
            "raise_",
        ):
            target.raise_()

    def activateWindow(
        self,
    ) -> None:
        target = self._target()

        if hasattr(
            target,
            "activateWindow",
        ):
            target.activateWindow()


def prepare_desktop_ui(
    *,
    qapp,
    desktop,
) -> None:
    apply_light_theme(
        qapp
    )

    desktop.show()


class DesktopApplication:
    """
    Top-level desktop application controller.

    Production remains closed until onboarding and
    the historical baseline are complete.
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
        settings_window: WindowLike
        | None = None,
        tray_controller=None,
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

        self.tray_controller = (
            tray_controller
        )

        self._scheduler_started = False
        self._tray_started = False

    def _show_tray_once(
        self,
    ) -> None:
        if (
            self.tray_controller
            is None
            or self._tray_started
        ):
            return

        self.tray_controller.show()

        self._tray_started = True

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
        self._show_tray_once()

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


def _source_autostart_command() -> str:
    """
    Development:
        python run_desktop.py

    Packaged:
        bundled executable
    """

    if getattr(
        sys,
        "frozen",
        False,
    ):
        return (
            f'"{sys.executable}"'
        )

    script = (
        Path(__file__)
        .resolve()
        .parent
        .parent
        / "run_desktop.py"
    )

    if sys.platform.startswith(
        "win"
    ):
        return (
            f'"{sys.executable}" '
            f'"{script}"'
        )

    return shlex.join(
        [
            sys.executable,
            str(script),
        ]
    )


def create_application(
    paths: DesktopPaths
    | None = None,
    *,
    credentials=None,
    qapp=None,
    runner=None,
    autostart_adapter=None,
    enable_tray: bool = True,
) -> DesktopApplication:
    """
    Assemble the real Desktop V1 application.

    No .env dependency is used here.

    Runtime:
        DesktopPaths

    Non-secrets:
        SettingsStore

    Secrets:
        Keychain / Credential Manager

    Business workflow:
        DesktopCoreBridge

    Polling:
        DesktopScheduler + QtThreadPoolRunner
    """

    qapp = (
        qapp
        or QApplication.instance()
    )

    if qapp is None:
        raise RuntimeError(
            "QApplication must exist before "
            "create_application()"
        )

    paths = (
        paths
        or DesktopPaths.for_current_user()
    )

    paths.ensure()

    credentials = (
        credentials
        or KeyringCredentialStore()
    )

    settings_store = SettingsStore(
        paths.settings_file
    )

    configuration = (
        DesktopConfiguration(
            settings_store=(
                settings_store
            ),
            credentials=(
                credentials
            ),
        )
    )

    onboarding_service = (
        OnboardingService(
            settings_store=(
                settings_store
            ),
            credential_store=(
                credentials
            ),
            paths=paths,
            core_bridge_factory=(
                DesktopCoreBridge
            ),
        )
    )

    setup_controller = (
        DesktopSetupController(
            configuration=(
                configuration
            ),
            paths=paths,
            onboarding_service=(
                onboarding_service
            ),
        )
    )

    health_tracker = (
        HealthTracker()
    )

    runner = (
        runner
        or QtThreadPoolRunner()
    )

    if autostart_adapter is None:
        autostart_adapter = (
            create_autostart_adapter()
        )

    holder = {}
    runtime_refs = {}

    runtime_state = {
        "status": (
            AppStatus.RUNNING
            if setup_controller
            .is_ready_for_production()
            else AppStatus
            .WAITING_INITIALIZATION
        ),
        "last_check_at": "",
        "next_check_at": "",
        "today_scanned": 0,
        "today_new_inquiries": 0,
        "today_drafts": 0,
    }

    def dashboard_snapshot():
        settings = (
            configuration.reload()
        )

        return DashboardSnapshot(
            status=(
                runtime_state[
                    "status"
                ]
            ),
            last_check_at=(
                runtime_state[
                    "last_check_at"
                ]
            ),
            next_check_at=(
                runtime_state[
                    "next_check_at"
                ]
            ),
            today_scanned=(
                runtime_state[
                    "today_scanned"
                ]
            ),
            today_new_inquiries=(
                runtime_state[
                    "today_new_inquiries"
                ]
            ),
            today_drafts=(
                runtime_state[
                    "today_drafts"
                ]
            ),
            history_ready=(
                settings.baseline_completed
            ),
            style_ready=(
                settings.baseline_completed
            ),
            wecom_connected=(
                configuration
                .is_wecom_configured()
            ),
        )

    def render_dashboard():
        dashboard = holder.get(
            "dashboard"
        )

        if dashboard is None:
            return

        dashboard.render(
            dashboard_snapshot()
        )

    def run_operation(
        operation,
    ):
        """
        Execute blocking IMAP/AI/history work in
        QThreadPool while the Qt event loop stays alive.
        """

        loop = QEventLoop()

        state = {
            "result": None,
            "error": None,
        }

        def success(
            result,
        ):
            state["result"] = result
            loop.quit()

        def failure(
            error,
        ):
            state["error"] = error
            loop.quit()

        accepted = runner.submit(
            operation,
            success,
            failure,
        )

        if accepted is False:
            raise RuntimeError(
                "background operation was rejected"
            )

        loop.exec()

        if state["error"] is not None:
            raise state["error"]

        return state["result"]

    def fresh_bridge():
        return DesktopCoreBridge(
            settings=(
                configuration.reload()
            ),
            credentials=credentials,
            paths=paths,
        )

    def production_cycle():
        return (
            fresh_bridge()
            .run_mail_cycle()
        )

    def cycle_result(
        result,
    ):
        runtime_state[
            "today_scanned"
        ] += int(
            result.get(
                "total",
                0,
            )
        )

        processed = int(
            result.get(
                "processed",
                0,
            )
        )

        runtime_state[
            "today_new_inquiries"
        ] += processed

        runtime_state[
            "today_drafts"
        ] += processed

        runtime_state[
            "last_check_at"
        ] = "刚刚"

        interval = (
            configuration.settings
            .poll_interval_seconds
        )

        runtime_state[
            "next_check_at"
        ] = (
            f"{max(1, interval // 60)} 分钟后"
        )

        runtime_state[
            "status"
        ] = health_tracker.status(
            AppStatus.RUNNING
        )

        render_dashboard()

    def cycle_error(
        error,
    ):
        del error

        runtime_state[
            "last_check_at"
        ] = "刚刚"

        runtime_state[
            "status"
        ] = health_tracker.status(
            AppStatus.RUNNING
        )

        render_dashboard()

    scheduler = DesktopScheduler(
        interval_seconds=(
            configuration.settings
            .poll_interval_seconds
        ),
        cycle=production_cycle,
        on_result=cycle_result,
        on_error=cycle_error,
        timer_factory=(
            qt_timer_factory
        ),
        ready_check=(
            setup_controller
            .is_ready_for_production
        ),
        health_tracker=(
            health_tracker
        ),
        health_service=(
            ServiceName.MAIL
        ),
        runner=runner,
    )

    holder[
        "scheduler"
    ] = scheduler

    def set_status(
        status,
    ):
        runtime_state[
            "status"
        ] = status

        render_dashboard()

    def pause_work():
        holder[
            "desktop"
        ].pause()

        set_status(
            AppStatus.PAUSED
        )

    def resume_work():
        holder[
            "desktop"
        ].resume()

        set_status(
            AppStatus.RUNNING
        )

    def run_now():
        return holder[
            "desktop"
        ].run_now()

    dashboard = DashboardWindow(
        on_pause=pause_work,
        on_resume=resume_work,
        on_run_now=run_now,
        on_settings=lambda: (
            holder[
                "desktop"
            ].open_settings()
        ),
    )

    holder[
        "dashboard"
    ] = dashboard

    def save_advanced(
        updated,
    ):
        old_interval = (
            scheduler.interval_seconds
        )

        setup_controller.save_advanced_settings(
            updated
        )

        scheduler.interval_seconds = (
            updated
            .poll_interval_seconds
        )

        if (
            scheduler.is_running
            and old_interval
            != scheduler.interval_seconds
        ):
            scheduler.stop()
            scheduler.start()

        render_dashboard()

    def open_advanced_settings(
        parent=None,
    ):
        unlock = AdminUnlockDialog(
            on_verify=(
                setup_controller
                .verify_admin_pin
            ),
            on_unlocked=lambda: None,
            parent=parent,
        )

        runtime_refs[
            "admin_unlock_dialog"
        ] = unlock

        accepted = (
            unlock.exec()
            == QDialog.DialogCode.Accepted
        )

        if not accepted:
            return

        advanced = (
            AdvancedSettingsDialog(
                settings=(
                    configuration.reload()
                ),
                credentials=credentials,
                on_save=save_advanced,
                parent=parent,
            )
        )

        runtime_refs[
            "advanced_settings_dialog"
        ] = advanced

        advanced.exec()

        configuration.reload()

        render_dashboard()

    onboarding_holder = {}

    def configure_ai():
        open_advanced_settings(
            onboarding_holder.get(
                "window"
            )
        )

    def complete_onboarding():
        configuration.reload()

        set_status(
            AppStatus.RUNNING
        )

        holder[
            "desktop"
        ].on_onboarding_complete()

    onboarding = OnboardingWindow(
        on_test_mail=(
            lambda email, auth: (
                run_operation(
                    lambda: (
                        setup_controller
                        .test_and_save_mail(
                            email,
                            auth,
                        )
                    )
                )
            )
        ),
        on_save_identity=(
            setup_controller
            .save_identity
        ),
        is_ai_configured=(
            setup_controller
            .is_ai_configured
        ),
        on_test_wecom=(
            lambda webhook: (
                run_operation(
                    lambda: (
                        setup_controller
                        .test_and_save_wecom(
                            webhook
                        )
                    )
                )
            )
        ),
        on_learn_history=(
            lambda: (
                run_operation(
                    setup_controller
                    .learn_history
                )
            )
        ),
        on_complete=(
            complete_onboarding
        ),
        on_create_pin=(
            setup_controller
            .create_admin_pin
        ),
        on_configure_ai=(
            configure_ai
        ),
    )

    onboarding_holder[
        "window"
    ] = onboarding

    def save_boolean_setting(
        field_name,
        value,
    ):
        settings = deepcopy(
            configuration.reload()
        )

        setattr(
            settings,
            field_name,
            bool(value),
        )

        configuration.save_settings(
            settings
        )

    def toggle_autostart(
        enabled,
    ):
        if enabled:
            autostart_adapter.enable(
                _source_autostart_command()
            )

        else:
            autostart_adapter.disable()

        save_boolean_setting(
            "autostart_enabled",
            enabled,
        )

    def test_saved_mail():
        return bool(
            run_operation(
                lambda: (
                    fresh_bridge()
                    .verify_mail()
                )
            )
        )

    def test_saved_wecom():
        return bool(
            run_operation(
                lambda: (
                    fresh_bridge()
                    .test_wecom()
                )
            )
        )

    def relearn_history():
        run_operation(
            setup_controller
            .learn_history
        )

        configuration.reload()

        render_dashboard()

    def open_settings():
        settings = (
            configuration.reload()
        )

        settings_dialog_holder = {}

        dialog = SettingsDialog(
            settings=settings,
            on_save_identity=(
                setup_controller
                .save_identity
            ),
            on_toggle_autostart=(
                toggle_autostart
            ),
            on_toggle_desktop_notifications=(
                lambda enabled: (
                    save_boolean_setting(
                        "desktop_notifications_enabled",
                        enabled,
                    )
                )
            ),
            on_test_mail=(
                test_saved_mail
            ),
            on_test_wecom=(
                test_saved_wecom
            ),
            on_relearn_history=(
                relearn_history
            ),
            on_open_admin=(
                lambda: (
                    open_advanced_settings(
                        settings_dialog_holder[
                            "dialog"
                        ]
                    )
                )
            ),
        )

        settings_dialog_holder[
            "dialog"
        ] = dialog

        runtime_refs[
            "settings_dialog"
        ] = dialog

        dialog.show()

    settings_proxy = (
        _CallbackWindow(
            open_settings
        )
    )

    desktop = DesktopApplication(
        dashboard_window=dashboard,
        onboarding_window=onboarding,
        settings_window=(
            settings_proxy
        ),
        scheduler=scheduler,
        ready_check=(
            setup_controller
            .is_ready_for_production
        ),
    )

    holder[
        "desktop"
    ] = desktop

    tray_controller = None

    if enable_tray:
        qapp.setQuitOnLastWindowClosed(
            False
        )

        primary_window = (
            _PrimaryWindowRouter(
                dashboard=dashboard,
                onboarding=onboarding,
                ready_check=(
                    setup_controller
                    .is_ready_for_production
                ),
            )
        )

        tray_controller = (
            TrayController(
                window=primary_window,
                scheduler=scheduler,
                on_settings=(
                    desktop.open_settings
                ),
                on_quit=(
                    qapp.quit
                ),
            )
        )

        desktop.tray_controller = (
            tray_controller
        )

        dashboard.set_close_to_tray(
            True
        )

    #
    # Keep real production dependencies alive and
    # expose them for diagnostics/tests.
    #
    desktop.paths = paths
    desktop.credentials = credentials
    desktop.settings_store = (
        settings_store
    )
    desktop.configuration = (
        configuration
    )
    desktop.onboarding_service = (
        onboarding_service
    )
    desktop.setup_controller = (
        setup_controller
    )
    desktop.health_tracker = (
        health_tracker
    )
    desktop.runner = runner
    desktop.autostart_adapter = (
        autostart_adapter
    )
    desktop.runtime_refs = (
        runtime_refs
    )

    render_dashboard()

    return desktop


def main() -> int:
    app = (
        QApplication.instance()
        or QApplication(
            sys.argv
        )
    )

    desktop = create_application(
        qapp=app
    )

    prepare_desktop_ui(
        qapp=app,
        desktop=desktop,
    )

    return app.exec()
