from collections.abc import Callable

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
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


class AdminUnlockDialog(QDialog):
    """
    Administrator six-digit PIN gate.

    The PIN is passed to the verification callback and
    is never persisted by the UI.
    """

    def __init__(
        self,
        *,
        on_verify: Callable[
            [str],
            bool,
        ],
        on_unlocked: Callable[
            [],
            None,
        ],
        parent=None,
    ) -> None:
        super().__init__(
            parent
        )

        self._on_verify = (
            on_verify
        )

        self._on_unlocked = (
            on_unlocked
        )

        self.setWindowTitle(
            "管理员验证"
        )

        self.setModal(
            True
        )

        self.resize(
            460,
            280,
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
            24,
            22,
            24,
            22,
        )

        layout.setSpacing(
            12
        )

        title = QLabel(
            "进入高级设置"
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
            "高级设置可能影响邮箱、AI 和自动处理流程。"
            "请输入 6 位管理员 PIN 继续。"
        )

        description.setWordWrap(
            True
        )

        description.setProperty(
            "role",
            "muted",
        )

        self.pin_edit = QLineEdit()

        self.pin_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.pin_edit.setMaxLength(
            6
        )

        self.pin_edit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(
                    r"[0-9]{0,6}"
                )
            )
        )

        self.pin_edit.setPlaceholderText(
            "6 位管理员 PIN"
        )

        #
        # Temporary compatibility for any old UI test or
        # integration still referring to password_edit.
        #
        self.password_edit = (
            self.pin_edit
        )

        self.status_label = QLabel(
            ""
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

        self.unlock_button = QPushButton(
            "验证并进入"
        )

        self.unlock_button.setProperty(
            "role",
            "primary",
        )

        cancel_button.clicked.connect(
            self.reject
        )

        self.unlock_button.clicked.connect(
            self._unlock
        )

        self.pin_edit.returnPressed.connect(
            self._unlock
        )

        actions.addWidget(
            cancel_button
        )

        actions.addWidget(
            self.unlock_button
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
            self.pin_edit
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

    def _unlock(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        value = (
            self.pin_edit.text()
        )

        if (
            len(value) != 6
            or not value.isdigit()
        ):
            self.status_label.setText(
                "请输入 6 位管理员 PIN"
            )

            self.status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            return

        try:
            success = bool(
                self._on_verify(
                    value
                )
            )

        except Exception:
            success = False

        if not success:
            self.status_label.setText(
                "管理员 PIN 错误"
            )

            self.status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            self.pin_edit.selectAll()
            self.pin_edit.setFocus()

            return

        self.status_label.setText(
            "验证成功"
        )

        self.status_label.setStyleSheet(
            f"color: {LIGHT_TOKENS.success};"
        )

        self._on_unlocked()

        self.accept()
