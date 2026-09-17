from collections.abc import Callable

from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QStyle,
    QSystemTrayIcon,
)


class TrayController:
    """
    System-tray controller.

    Tray actions reuse the same window and scheduler
    controllers as the main dashboard.
    """

    def __init__(
        self,
        *,
        window,
        scheduler,
        on_settings: Callable[
            [],
            None,
        ],
        on_quit: Callable[
            [],
            None,
        ],
        icon=None,
    ) -> None:
        self.window = window
        self.scheduler = scheduler
        self.on_settings_callback = (
            on_settings
        )
        self.on_quit_callback = (
            on_quit
        )

        app = QApplication.instance()

        if app is None:
            raise RuntimeError(
                "QApplication must exist "
                "before TrayController"
            )

        if icon is None:
            icon = (
                app.style().standardIcon(
                    QStyle.StandardPixmap.SP_ComputerIcon
                )
            )

        self.tray_icon = QSystemTrayIcon(
            icon
        )

        self.tray_icon.setToolTip(
            "外贸数字员工"
        )

        self.menu = QMenu()

        self.open_action = QAction(
            "打开外贸数字员工"
        )

        self.pause_action = QAction(
            "暂停工作"
        )

        self.run_now_action = QAction(
            "立即检查邮件"
        )

        self.settings_action = QAction(
            "设置"
        )

        self.quit_action = QAction(
            "退出外贸数字员工"
        )

        self.menu.addAction(
            self.open_action
        )

        self.menu.addSeparator()

        self.menu.addAction(
            self.pause_action
        )

        self.menu.addAction(
            self.run_now_action
        )

        self.menu.addAction(
            self.settings_action
        )

        self.menu.addSeparator()

        self.menu.addAction(
            self.quit_action
        )

        self.tray_icon.setContextMenu(
            self.menu
        )

        self.open_action.triggered.connect(
            self.open_window
        )

        self.pause_action.triggered.connect(
            self.toggle_pause
        )

        self.run_now_action.triggered.connect(
            self.run_now
        )

        self.settings_action.triggered.connect(
            self.open_settings
        )

        self.quit_action.triggered.connect(
            self.quit_application
        )

        self.tray_icon.activated.connect(
            self._activated
        )

        self._refresh_pause_text()

    def show(
        self,
    ) -> None:
        self.tray_icon.show()

    def hide(
        self,
    ) -> None:
        self.tray_icon.hide()

    def open_window(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self.window.show()

        if hasattr(
            self.window,
            "raise_",
        ):
            self.window.raise_()

        if hasattr(
            self.window,
            "activateWindow",
        ):
            self.window.activateWindow()

    def _refresh_pause_text(
        self,
    ) -> None:
        paused = bool(
            getattr(
                self.scheduler,
                "is_paused",
                False,
            )
        )

        self.pause_action.setText(
            (
                "继续工作"
                if paused
                else "暂停工作"
            )
        )

    def toggle_pause(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if bool(
            getattr(
                self.scheduler,
                "is_paused",
                False,
            )
        ):
            self.scheduler.resume()

        else:
            self.scheduler.pause()

        self._refresh_pause_text()

    def run_now(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self.scheduler.run_now()

    def open_settings(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self.on_settings_callback()

    def quit_application(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self.scheduler.stop()

        self.tray_icon.hide()

        self.on_quit_callback()

    def _activated(
        self,
        reason,
    ) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.open_window()
