from collections.abc import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.models import DesktopSettings
from desktop.ui.components import (
    Card,
    SectionTitle,
)


class SettingsDialog(QDialog):
    """
    Normal-user settings.

    Advanced technical configuration and secrets
    are intentionally not exposed here.
    """

    def __init__(
        self,
        *,
        settings: DesktopSettings,
        on_save_identity: Callable[
            [str, str, str],
            None,
        ],
        on_toggle_autostart: Callable[
            [bool],
            None,
        ],
        on_toggle_desktop_notifications: Callable[
            [bool],
            None,
        ],
        on_test_mail: Callable[
            [],
            bool,
        ],
        on_test_wecom: Callable[
            [],
            bool,
        ],
        on_relearn_history: Callable[
            [],
            None,
        ],
        on_open_admin: Callable[
            [],
            None,
        ],
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._on_save_identity = (
            on_save_identity
        )

        self._on_toggle_autostart = (
            on_toggle_autostart
        )

        self._on_toggle_desktop_notifications = (
            on_toggle_desktop_notifications
        )

        self._on_test_mail = (
            on_test_mail
        )

        self._on_test_wecom = (
            on_test_wecom
        )

        self._on_relearn_history = (
            on_relearn_history
        )

        self._on_open_admin = (
            on_open_admin
        )

        self.setWindowTitle(
            "设置"
        )

        self.resize(
            760,
            720,
        )

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            28,
            26,
            28,
            26,
        )

        root.setSpacing(
            16
        )

        title = QLabel(
            "设置"
        )

        title_font = title.font()

        title_font.setPointSize(
            20
        )

        title_font.setBold(
            True
        )

        title.setFont(
            title_font
        )

        root.addWidget(
            title
        )

        #
        # Account
        #
        account_card = Card()

        account_layout = QVBoxLayout(
            account_card
        )

        account_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        account_layout.setSpacing(
            10
        )

        account_layout.addWidget(
            SectionTitle(
                "账户"
            )
        )

        account_row = QHBoxLayout()

        account_row.addWidget(
            QLabel(
                "163 邮箱"
            )
        )

        account_row.addStretch(
            1
        )

        self.email_value_label = QLabel(
            settings.email_user
            or "未配置"
        )

        self.email_value_label.setProperty(
            "role",
            "muted",
        )

        account_row.addWidget(
            self.email_value_label
        )

        self.test_mail_button = QPushButton(
            "测试连接"
        )

        self.test_mail_button.setProperty(
            "role",
            "secondary",
        )

        self.test_mail_button.clicked.connect(
            self._test_mail
        )

        account_row.addWidget(
            self.test_mail_button
        )

        account_layout.addLayout(
            account_row
        )

        self.mail_status_label = QLabel(
            ""
        )

        self.mail_status_label.setProperty(
            "role",
            "muted",
        )

        account_layout.addWidget(
            self.mail_status_label
        )

        root.addWidget(
            account_card
        )

        #
        # Identity
        #
        identity_card = Card()

        identity_layout = QVBoxLayout(
            identity_card
        )

        identity_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        identity_layout.setSpacing(
            10
        )

        identity_layout.addWidget(
            SectionTitle(
                "个人信息"
            )
        )

        identity_layout.addWidget(
            QLabel(
                "姓名"
            )
        )

        self.name_edit = QLineEdit(
            settings.sender_name
        )

        identity_layout.addWidget(
            self.name_edit
        )

        identity_layout.addWidget(
            QLabel(
                "职位"
            )
        )

        self.title_edit = QLineEdit(
            settings.sender_title
        )

        identity_layout.addWidget(
            self.title_edit
        )

        identity_layout.addWidget(
            QLabel(
                "公司"
            )
        )

        self.company_edit = QLineEdit(
            settings.sender_company
        )

        identity_layout.addWidget(
            self.company_edit
        )

        identity_actions = QHBoxLayout()

        identity_actions.addStretch(
            1
        )

        self.save_identity_button = QPushButton(
            "保存个人信息"
        )

        self.save_identity_button.setProperty(
            "role",
            "primary",
        )

        self.save_identity_button.clicked.connect(
            self._save_identity
        )

        identity_actions.addWidget(
            self.save_identity_button
        )

        identity_layout.addLayout(
            identity_actions
        )

        root.addWidget(
            identity_card
        )

        #
        # Preferences
        #
        preferences_card = Card()

        preferences_layout = QVBoxLayout(
            preferences_card
        )

        preferences_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        preferences_layout.setSpacing(
            12
        )

        preferences_layout.addWidget(
            SectionTitle(
                "工作方式"
            )
        )

        self.autostart_checkbox = QCheckBox(
            "开机自动启动"
        )

        self.autostart_checkbox.setChecked(
            settings.autostart_enabled
        )

        self.notifications_checkbox = QCheckBox(
            "桌面通知"
        )

        self.notifications_checkbox.setChecked(
            settings.desktop_notifications_enabled
        )

        self.autostart_checkbox.toggled.connect(
            self._on_toggle_autostart
        )

        self.notifications_checkbox.toggled.connect(
            self._on_toggle_desktop_notifications
        )

        preferences_layout.addWidget(
            self.autostart_checkbox
        )

        preferences_layout.addWidget(
            self.notifications_checkbox
        )

        root.addWidget(
            preferences_card
        )

        #
        # Learning / WeCom
        #
        learning_card = Card()

        learning_layout = QVBoxLayout(
            learning_card
        )

        learning_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        learning_layout.setSpacing(
            10
        )

        learning_layout.addWidget(
            SectionTitle(
                "学习与通知"
            )
        )

        history_row = QHBoxLayout()

        history_row.addWidget(
            QLabel(
                "历史邮件"
            )
        )

        history_row.addStretch(
            1
        )

        history_status = QLabel(
            (
                "已学习"
                if settings.baseline_completed
                else "未完成"
            )
        )

        history_status.setProperty(
            "role",
            "muted",
        )

        history_row.addWidget(
            history_status
        )

        learning_layout.addLayout(
            history_row
        )

        wecom_row = QHBoxLayout()

        wecom_row.addWidget(
            QLabel(
                "企业微信"
            )
        )

        wecom_row.addStretch(
            1
        )

        self.test_wecom_button = QPushButton(
            "测试通知"
        )

        self.test_wecom_button.setProperty(
            "role",
            "secondary",
        )

        self.test_wecom_button.clicked.connect(
            self._test_wecom
        )

        wecom_row.addWidget(
            self.test_wecom_button
        )

        learning_layout.addLayout(
            wecom_row
        )

        self.wecom_status_label = QLabel(
            ""
        )

        self.wecom_status_label.setProperty(
            "role",
            "muted",
        )

        learning_layout.addWidget(
            self.wecom_status_label
        )

        learning_actions = QHBoxLayout()

        learning_actions.addStretch(
            1
        )

        self.relearn_button = QPushButton(
            "重新学习历史邮件"
        )

        self.relearn_button.setProperty(
            "role",
            "secondary",
        )

        self.relearn_button.clicked.connect(
            self._relearn
        )

        learning_actions.addWidget(
            self.relearn_button
        )

        learning_layout.addLayout(
            learning_actions
        )

        root.addWidget(
            learning_card
        )

        #
        # Admin
        #
        admin_row = QHBoxLayout()

        admin_hint = QLabel(
            "高级技术配置仅供管理员使用"
        )

        admin_hint.setProperty(
            "role",
            "muted",
        )

        admin_row.addWidget(
            admin_hint
        )

        admin_row.addStretch(
            1
        )

        self.admin_button = QPushButton(
            "高级设置"
        )

        self.admin_button.setProperty(
            "role",
            "secondary",
        )

        self.admin_button.clicked.connect(
            self._open_admin
        )

        admin_row.addWidget(
            self.admin_button
        )

        root.addLayout(
            admin_row
        )

    def _save_identity(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self._on_save_identity(
            self.name_edit.text().strip(),
            self.title_edit.text().strip(),
            self.company_edit.text().strip(),
        )

    def _test_mail(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        try:
            success = bool(
                self._on_test_mail()
            )
        except Exception:
            success = False

        self.mail_status_label.setText(
            (
                "邮箱连接正常"
                if success
                else "邮箱连接失败"
            )
        )

    def _test_wecom(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        try:
            success = bool(
                self._on_test_wecom()
            )
        except Exception:
            success = False

        self.wecom_status_label.setText(
            (
                "企业微信连接正常"
                if success
                else "企业微信连接失败"
            )
        )

    def _relearn(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self._on_relearn_history()

    def _open_admin(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self._on_open_admin()
