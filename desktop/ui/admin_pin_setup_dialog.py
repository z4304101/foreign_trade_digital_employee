from collections.abc import Callable

from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from desktop.ui.components import Card
from desktop.ui.theme import LIGHT_TOKENS


class AdminPinSetupDialog(QDialog):
    """
    First-time administrator PIN creation.

    The UI never persists the PIN itself. A validated
    six-digit value is passed to the injected callback.
    """

    def __init__(
        self,
        *,
        on_create: Callable[
            [str],
            None,
        ],
        parent=None,
    ) -> None:
        super().__init__(
            parent
        )

        self._on_create = (
            on_create
        )

        self.setWindowTitle(
            "创建管理员 PIN"
        )

        self.setModal(
            True
        )

        self.resize(
            500,
            360,
        )

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        card = Card()

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            26,
            24,
            26,
            24,
        )

        layout.setSpacing(
            12
        )

        title = QLabel(
            "创建管理员 PIN"
        )

        font = title.font()
        font.setPointSize(
            17
        )
        font.setBold(
            True
        )
        title.setFont(
            font
        )

        description = QLabel(
            "请设置 6 位数字 PIN。"
            "以后进入高级设置时需要使用这个 PIN。"
        )

        description.setWordWrap(
            True
        )

        description.setProperty(
            "role",
            "muted",
        )

        validator = QRegularExpressionValidator(
            QRegularExpression(
                r"[0-9]{0,6}"
            )
        )

        self.pin_edit = QLineEdit()

        self.pin_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.pin_edit.setMaxLength(
            6
        )

        self.pin_edit.setValidator(
            validator
        )

        self.pin_edit.setPlaceholderText(
            "输入 6 位数字 PIN"
        )

        self.confirm_pin_edit = QLineEdit()

        self.confirm_pin_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.confirm_pin_edit.setMaxLength(
            6
        )

        self.confirm_pin_edit.setValidator(
            validator
        )

        self.confirm_pin_edit.setPlaceholderText(
            "再次输入 PIN"
        )

        self.status_label = QLabel(
            "PIN 不会以明文保存"
        )

        self.status_label.setProperty(
            "role",
            "muted",
        )

        actions = QHBoxLayout()

        actions.addStretch(
            1
        )

        cancel_button = QPushButton(
            "取消"
        )

        cancel_button.setProperty(
            "role",
            "secondary",
        )

        self.create_button = QPushButton(
            "创建 PIN"
        )

        self.create_button.setProperty(
            "role",
            "primary",
        )

        self.create_button.setEnabled(
            False
        )

        self.pin_edit.textChanged.connect(
            self._refresh_state
        )

        self.confirm_pin_edit.textChanged.connect(
            self._refresh_state
        )

        cancel_button.clicked.connect(
            self.reject
        )

        self.create_button.clicked.connect(
            self._create
        )

        actions.addWidget(
            cancel_button
        )

        actions.addWidget(
            self.create_button
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            description
        )

        layout.addSpacing(
            6
        )

        layout.addWidget(
            QLabel(
                "管理员 PIN"
            )
        )

        layout.addWidget(
            self.pin_edit
        )

        layout.addWidget(
            QLabel(
                "确认 PIN"
            )
        )

        layout.addWidget(
            self.confirm_pin_edit
        )

        layout.addWidget(
            self.status_label
        )

        layout.addStretch(
            1
        )

        layout.addLayout(
            actions
        )

        root.addWidget(
            card
        )

    def _refresh_state(
        self,
        _text: str = "",
    ) -> None:
        pin = (
            self.pin_edit.text()
        )

        confirmation = (
            self.confirm_pin_edit.text()
        )

        pin_complete = (
            len(pin) == 6
            and pin.isdigit()
        )

        confirmation_complete = (
            len(confirmation) == 6
            and confirmation.isdigit()
        )

        if (
            confirmation
            and pin != confirmation
        ):
            self.status_label.setText(
                "两次输入的 PIN 不一致"
            )

            self.status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

        elif (
            pin_complete
            and confirmation_complete
            and pin == confirmation
        ):
            self.status_label.setText(
                "PIN 可以创建"
            )

            self.status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.success};"
            )

        else:
            self.status_label.setText(
                "请输入并确认 6 位数字 PIN"
            )

            self.status_label.setStyleSheet(
                ""
            )

        self.create_button.setEnabled(
            pin_complete
            and confirmation_complete
            and pin == confirmation
        )

    def _create(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if not self.create_button.isEnabled():
            return

        value = (
            self.pin_edit.text()
        )

        try:
            self._on_create(
                value
            )

        except Exception:
            self.status_label.setText(
                "PIN 创建失败，请重试"
            )

            self.status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            return

        self.accept()
