from copy import deepcopy
from collections.abc import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from desktop.credentials import (
    AI_API_KEY,
    WECOM_WEBHOOK,
    CredentialStore,
)
from desktop.models import DesktopSettings
from desktop.ui.components import (
    Card,
    SectionTitle,
)


class AdvancedSettingsDialog(QDialog):
    """
    Administrator-only technical settings.

    Existing secrets are never populated into text fields.
    Leaving a secret field blank preserves the current value.
    """

    def __init__(
        self,
        *,
        settings: DesktopSettings,
        credentials: CredentialStore,
        on_save: Callable[
            [DesktopSettings],
            None,
        ],
        parent=None,
    ) -> None:
        super().__init__(
            parent
        )

        self._settings = settings
        self._credentials = credentials
        self._on_save = on_save

        self.setWindowTitle(
            "高级设置"
        )

        self.resize(
            760,
            760,
        )

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            26,
            24,
            26,
            24,
        )

        root.setSpacing(
            14
        )

        title = QLabel(
            "高级设置"
        )

        font = title.font()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)

        hint = QLabel(
            "这些参数可能影响邮箱连接、AI 服务和自动处理流程。"
            "仅建议管理员修改。"
        )

        hint.setWordWrap(True)
        hint.setProperty(
            "role",
            "muted",
        )

        root.addWidget(title)
        root.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        content = QWidget()

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setSpacing(14)

        #
        # AI
        #
        ai_card = Card()

        ai_layout = QVBoxLayout(
            ai_card
        )

        ai_layout.addWidget(
            SectionTitle(
                "AI 服务"
            )
        )

        ai_form = QFormLayout()

        self.provider_edit = QLineEdit(
            settings.llm_provider
        )

        self.model_edit = QLineEdit(
            settings.llm_model
        )

        self.base_url_edit = QLineEdit(
            settings.llm_base_url
        )

        self.api_key_edit = QLineEdit()

        self.api_key_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.api_key_edit.setPlaceholderText(
            "留空表示不修改现有 API Key"
        )

        ai_form.addRow(
            "Provider",
            self.provider_edit,
        )

        ai_form.addRow(
            "Model",
            self.model_edit,
        )

        ai_form.addRow(
            "Base URL",
            self.base_url_edit,
        )

        ai_form.addRow(
            "API Key",
            self.api_key_edit,
        )

        ai_layout.addLayout(
            ai_form
        )

        content_layout.addWidget(
            ai_card
        )

        #
        # Mail
        #
        mail_card = Card()

        mail_layout = QVBoxLayout(
            mail_card
        )

        mail_layout.addWidget(
            SectionTitle(
                "邮箱高级参数"
            )
        )

        mail_form = QFormLayout()

        self.imap_host_edit = QLineEdit(
            settings.imap_host
        )

        self.imap_port_spin = QSpinBox()

        self.imap_port_spin.setRange(
            1,
            65535,
        )

        self.imap_port_spin.setValue(
            settings.imap_port
        )

        mail_form.addRow(
            "IMAP Host",
            self.imap_host_edit,
        )

        mail_form.addRow(
            "IMAP Port",
            self.imap_port_spin,
        )

        mail_layout.addLayout(
            mail_form
        )

        content_layout.addWidget(
            mail_card
        )

        #
        # Notifications
        #
        notify_card = Card()

        notify_layout = QVBoxLayout(
            notify_card
        )

        notify_layout.addWidget(
            SectionTitle(
                "企业微信"
            )
        )

        self.webhook_edit = QLineEdit()

        self.webhook_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.webhook_edit.setPlaceholderText(
            "留空表示不修改现有 Webhook"
        )

        notify_layout.addWidget(
            self.webhook_edit
        )

        content_layout.addWidget(
            notify_card
        )

        #
        # Runtime
        #
        runtime_card = Card()

        runtime_layout = QVBoxLayout(
            runtime_card
        )

        runtime_layout.addWidget(
            SectionTitle(
                "自动工作"
            )
        )

        runtime_form = QFormLayout()

        self.poll_interval_spin = QSpinBox()

        self.poll_interval_spin.setRange(
            60,
            3600,
        )

        self.poll_interval_spin.setSuffix(
            " 秒"
        )

        self.poll_interval_spin.setValue(
            settings.poll_interval_seconds
        )

        runtime_form.addRow(
            "检查间隔",
            self.poll_interval_spin,
        )

        runtime_layout.addLayout(
            runtime_form
        )

        content_layout.addWidget(
            runtime_card
        )

        #
        # History
        #
        history_card = Card()

        history_layout = QVBoxLayout(
            history_card
        )

        history_layout.addWidget(
            SectionTitle(
                "历史学习"
            )
        )

        history_form = QFormLayout()

        self.history_months_spin = QSpinBox()

        self.history_months_spin.setRange(
            1,
            36,
        )

        self.history_months_spin.setValue(
            settings.history_months
        )

        self.history_limit_spin = QSpinBox()

        self.history_limit_spin.setRange(
            100,
            10000,
        )

        self.history_limit_spin.setValue(
            settings.history_limit
        )

        history_form.addRow(
            "学习月份",
            self.history_months_spin,
        )

        history_form.addRow(
            "邮件上限",
            self.history_limit_spin,
        )

        history_layout.addLayout(
            history_form
        )

        content_layout.addWidget(
            history_card
        )

        #
        # Diagnostics
        #
        diagnostics_card = Card()

        diagnostics_layout = QVBoxLayout(
            diagnostics_card
        )

        diagnostics_layout.addWidget(
            SectionTitle(
                "诊断"
            )
        )

        diagnostics_form = QFormLayout()

        self.log_level_combo = QComboBox()

        self.log_level_combo.addItems(
            [
                "DEBUG",
                "INFO",
                "WARNING",
                "ERROR",
            ]
        )

        index = (
            self.log_level_combo.findText(
                settings.log_level
            )
        )

        if index >= 0:
            self.log_level_combo.setCurrentIndex(
                index
            )

        diagnostics_form.addRow(
            "日志级别",
            self.log_level_combo,
        )

        diagnostics_layout.addLayout(
            diagnostics_form
        )

        content_layout.addWidget(
            diagnostics_card
        )

        content_layout.addStretch(1)

        scroll.setWidget(
            content
        )

        root.addWidget(
            scroll,
            1,
        )

        actions = QHBoxLayout()

        actions.addStretch(1)

        cancel_button = QPushButton(
            "取消"
        )

        cancel_button.setProperty(
            "role",
            "secondary",
        )

        self.save_button = QPushButton(
            "保存高级设置"
        )

        self.save_button.setProperty(
            "role",
            "primary",
        )

        cancel_button.clicked.connect(
            self.reject
        )

        self.save_button.clicked.connect(
            self._save
        )

        actions.addWidget(
            cancel_button
        )

        actions.addWidget(
            self.save_button
        )

        root.addLayout(
            actions
        )

    def _save(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        updated = deepcopy(
            self._settings
        )

        updated.imap_host = (
            self.imap_host_edit.text().strip()
        )

        updated.imap_port = (
            self.imap_port_spin.value()
        )

        updated.llm_provider = (
            self.provider_edit.text().strip()
        )

        updated.llm_model = (
            self.model_edit.text().strip()
        )

        updated.llm_base_url = (
            self.base_url_edit.text().strip()
        )

        updated.poll_interval_seconds = (
            self.poll_interval_spin.value()
        )

        updated.history_months = (
            self.history_months_spin.value()
        )

        updated.history_limit = (
            self.history_limit_spin.value()
        )

        updated.log_level = (
            self.log_level_combo.currentText()
        )

        api_key = (
            self.api_key_edit.text().strip()
        )

        if api_key:
            self._credentials.set(
                AI_API_KEY,
                api_key,
            )

        webhook = (
            self.webhook_edit.text().strip()
        )

        if webhook:
            self._credentials.set(
                WECOM_WEBHOOK,
                webhook,
            )

        self._on_save(
            updated
        )

        self.accept()
