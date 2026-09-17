from collections.abc import Callable
from typing import Any

from PySide6.QtCore import (
    QRegularExpression,
    Qt,
)
from PySide6.QtGui import (
    QRegularExpressionValidator,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.ui.components import (
    Card,
    SectionTitle,
)
from desktop.ui.theme import (
    LIGHT_TOKENS,
)


class OnboardingWindow(QMainWindow):
    """
    Fluent first-run onboarding wizard.

    Ordinary users only see the minimum configuration
    required to start using the product.

    Historical learning is mandatory before completion.

    This UI does not persist secrets itself. Secrets are
    passed to injected callbacks and are stored by the
    desktop service layer / operating-system credential
    store.
    """

    STEP_NAMES = (
        "邮箱",
        "身份",
        "管理员 PIN",
        "AI",
        "企业微信",
        "学习",
    )

    def __init__(
        self,
        *,
        on_test_mail: Callable[
            [str, str],
            bool,
        ],
        on_save_identity: Callable[
            [str, str, str],
            None,
        ],
        is_ai_configured: Callable[
            [],
            bool,
        ],
        on_test_wecom: Callable[
            [str],
            bool,
        ],
        on_learn_history: Callable[
            [],
            Any,
        ],
        on_complete: Callable[
            [],
            None,
        ],
        on_create_pin: Callable[
            [str],
            None,
        ]
        | None = None,
        on_configure_ai: Callable[
            [],
            None,
        ]
        | None = None,
    ) -> None:
        super().__init__()

        self._on_test_mail = on_test_mail
        self._on_save_identity = (
            on_save_identity
        )
        self._is_ai_configured = (
            is_ai_configured
        )
        self._on_test_wecom = (
            on_test_wecom
        )
        self._on_learn_history = (
            on_learn_history
        )
        self._on_complete = on_complete
        self._on_create_pin = on_create_pin
        self._on_configure_ai = on_configure_ai

        self.setWindowTitle(
            "外贸数字员工 · 首次配置"
        )

        self.resize(
            920,
            680,
        )

        self.setMinimumSize(
            820,
            620,
        )

        root = QWidget(self)
        root.setObjectName(
            "AppRoot"
        )

        root_layout = QVBoxLayout(
            root
        )

        root_layout.setContentsMargins(
            42,
            32,
            42,
            34,
        )

        root_layout.setSpacing(
            22
        )

        #
        # Brand header
        #
        brand_layout = QVBoxLayout()

        brand_layout.setSpacing(
            3
        )

        brand_label = QLabel(
            "外贸数字员工"
        )

        brand_font = (
            brand_label.font()
        )

        brand_font.setPointSize(
            21
        )

        brand_font.setBold(
            True
        )

        brand_label.setFont(
            brand_font
        )

        setup_label = QLabel(
            "首次配置"
        )

        setup_label.setProperty(
            "role",
            "muted",
        )

        brand_layout.addWidget(
            brand_label
        )

        brand_layout.addWidget(
            setup_label
        )

        root_layout.addLayout(
            brand_layout
        )

        #
        # Progress indicator
        #
        progress_layout = QHBoxLayout()

        progress_layout.setSpacing(
            8
        )

        self.step_labels: list[QLabel] = []

        for index, name in enumerate(
            self.STEP_NAMES
        ):
            label = QLabel(
                f"{index + 1}  {name}"
            )

            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            label.setMinimumHeight(
                34
            )

            label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )

            self.step_labels.append(
                label
            )

            progress_layout.addWidget(
                label
            )

        root_layout.addLayout(
            progress_layout
        )

        #
        # Pages
        #
        self.stack = QStackedWidget()

        self.stack.addWidget(
            self._build_mail_page()
        )

        self.stack.addWidget(
            self._build_identity_page()
        )

        self.stack.addWidget(
            self._build_pin_page()
        )

        self.stack.addWidget(
            self._build_ai_page()
        )

        self.stack.addWidget(
            self._build_wecom_page()
        )

        self.stack.addWidget(
            self._build_history_page()
        )

        root_layout.addWidget(
            self.stack,
            1,
        )

        self.setCentralWidget(
            root
        )

        self._set_step(
            0
        )

    #
    # Shared UI helpers
    #
    def _create_page(
        self,
        title: str,
        description: str,
    ):
        page = QWidget()

        outer = QHBoxLayout(
            page
        )

        outer.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        outer.addStretch(
            1
        )

        card = Card()

        card.setMinimumWidth(
            620
        )

        card.setMaximumWidth(
            720
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            34,
            30,
            34,
            30,
        )

        card_layout.setSpacing(
            14
        )

        title_label = SectionTitle(
            title
        )

        title_font = (
            title_label.font()
        )

        title_font.setPointSize(
            17
        )

        title_label.setFont(
            title_font
        )

        description_label = QLabel(
            description
        )

        description_label.setWordWrap(
            True
        )

        description_label.setProperty(
            "role",
            "muted",
        )

        card_layout.addWidget(
            title_label
        )

        card_layout.addWidget(
            description_label
        )

        card_layout.addSpacing(
            8
        )

        outer.addWidget(
            card
        )

        outer.addStretch(
            1
        )

        return (
            page,
            card_layout,
        )

    def _add_field_label(
        self,
        layout,
        text: str,
    ) -> None:
        label = QLabel(
            text
        )

        font = label.font()

        font.setBold(
            True
        )

        label.setFont(
            font
        )

        layout.addWidget(
            label
        )

    def _create_actions(
        self,
        layout,
    ) -> QHBoxLayout:
        actions = QHBoxLayout()

        actions.setSpacing(
            10
        )

        actions.addStretch(
            1
        )

        layout.addStretch(
            1
        )

        layout.addLayout(
            actions
        )

        return actions

    def _set_step(
        self,
        index: int,
    ) -> None:
        self.stack.setCurrentIndex(
            index
        )

        for step_index, label in enumerate(
            self.step_labels
        ):
            if step_index < index:
                label.setStyleSheet(
                    "QLabel {"
                    f"background: #ECFDF3;"
                    f"color: {LIGHT_TOKENS.success};"
                    "border: 1px solid #BBF7D0;"
                    "border-radius: 9px;"
                    "font-weight: 600;"
                    "padding: 4px 8px;"
                    "}"
                )

            elif step_index == index:
                label.setStyleSheet(
                    "QLabel {"
                    "background: #EFF6FF;"
                    f"color: {LIGHT_TOKENS.primary};"
                    "border: 1px solid #BFDBFE;"
                    "border-radius: 9px;"
                    "font-weight: 700;"
                    "padding: 4px 8px;"
                    "}"
                )

            else:
                label.setStyleSheet(
                    "QLabel {"
                    f"background: {LIGHT_TOKENS.surface};"
                    f"color: {LIGHT_TOKENS.text_secondary};"
                    f"border: 1px solid {LIGHT_TOKENS.border};"
                    "border-radius: 9px;"
                    "font-weight: 600;"
                    "padding: 4px 8px;"
                    "}"
                )

    #
    # Step 1: Mailbox
    #
    def _build_mail_page(
        self,
    ) -> QWidget:
        page, layout = self._create_page(
            "绑定你的 163 邮箱",
            (
                "数字员工只读取邮件并生成回复草稿，"
                "不会自动向客户发送邮件。"
            ),
        )

        self._add_field_label(
            layout,
            "邮箱地址",
        )

        self.email_edit = QLineEdit()

        self.email_edit.setPlaceholderText(
            "name@163.com"
        )

        layout.addWidget(
            self.email_edit
        )

        self._add_field_label(
            layout,
            "邮箱授权码",
        )

        self.auth_code_edit = QLineEdit()

        self.auth_code_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.auth_code_edit.setPlaceholderText(
            "请输入 163 邮箱授权码"
        )

        layout.addWidget(
            self.auth_code_edit
        )

        security_hint = QLabel(
            "授权码会保存到系统安全凭据中，不写入普通配置文件。"
        )

        security_hint.setWordWrap(
            True
        )

        security_hint.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            security_hint
        )

        self.email_status_label = QLabel(
            "尚未测试连接"
        )

        self.email_status_label.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            self.email_status_label
        )

        actions = self._create_actions(
            layout
        )

        self.test_mail_button = QPushButton(
            "测试连接"
        )

        self.test_mail_button.setProperty(
            "role",
            "secondary",
        )

        self.email_next_button = QPushButton(
            "下一步"
        )

        self.email_next_button.setProperty(
            "role",
            "primary",
        )

        self.email_next_button.setEnabled(
            False
        )

        self.test_mail_button.clicked.connect(
            self._test_mail
        )

        self.email_next_button.clicked.connect(
            lambda checked=False: self._set_step(1)
        )

        actions.addWidget(
            self.test_mail_button
        )

        actions.addWidget(
            self.email_next_button
        )

        return page

    def _test_mail(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        email = (
            self.email_edit.text().strip()
        )

        auth_code = (
            self.auth_code_edit.text()
        )

        try:
            success = bool(
                self._on_test_mail(
                    email,
                    auth_code,
                )
            )
        except Exception:
            success = False

        if success:
            self.email_status_label.setText(
                "邮箱连接正常"
            )

            self.email_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.success};"
            )

            self.email_next_button.setEnabled(
                True
            )

        else:
            self.email_status_label.setText(
                "邮箱连接失败，请检查邮箱和授权码"
            )

            self.email_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            self.email_next_button.setEnabled(
                False
            )

    #
    # Step 2: Identity
    #
    def _build_identity_page(
        self,
    ) -> QWidget:
        page, layout = self._create_page(
            "告诉数字员工你是谁",
            (
                "这些信息会用于回复草稿中的身份和签名。"
                "职位和公司可以留空。"
            ),
        )

        self._add_field_label(
            layout,
            "姓名",
        )

        self.name_edit = QLineEdit()

        self.name_edit.setPlaceholderText(
            "例如：Alice"
        )

        layout.addWidget(
            self.name_edit
        )

        self._add_field_label(
            layout,
            "职位（可选）",
        )

        self.title_edit = QLineEdit()

        self.title_edit.setPlaceholderText(
            "例如：Sales Manager"
        )

        layout.addWidget(
            self.title_edit
        )

        self._add_field_label(
            layout,
            "公司（可选）",
        )

        self.company_edit = QLineEdit()

        self.company_edit.setPlaceholderText(
            "例如：Example Co."
        )

        layout.addWidget(
            self.company_edit
        )

        actions = self._create_actions(
            layout
        )

        back_button = QPushButton(
            "上一步"
        )

        back_button.setProperty(
            "role",
            "secondary",
        )

        self.identity_next_button = QPushButton(
            "下一步"
        )

        self.identity_next_button.setProperty(
            "role",
            "primary",
        )

        back_button.clicked.connect(
            lambda checked=False: self._set_step(0)
        )

        self.identity_next_button.clicked.connect(
            self._save_identity
        )

        actions.addWidget(
            back_button
        )

        actions.addWidget(
            self.identity_next_button
        )

        return page

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

        self._set_step(
            2
        )

    #
    # Step 3: AI
    #
    def _build_ai_page(
        self,
    ) -> QWidget:
        page, layout = self._create_page(
            "AI 服务",
            (
                "AI 服务由管理员预先配置。"
                "普通用户不需要接触 API Key、模型或技术地址。"
            ),
        )

        self.ai_status_label = QLabel()

        status_font = (
            self.ai_status_label.font()
        )

        status_font.setPointSize(
            14
        )

        status_font.setBold(
            True
        )

        self.ai_status_label.setFont(
            status_font
        )

        layout.addWidget(
            self.ai_status_label
        )

        ai_hint = QLabel(
            "配置正常后，数字员工会使用 AI 分析新询盘并生成英文回复草稿。"
        )

        ai_hint.setWordWrap(
            True
        )

        ai_hint.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            ai_hint
        )

        actions = self._create_actions(
            layout
        )

        back_button = QPushButton(
            "上一步"
        )

        back_button.setProperty(
            "role",
            "secondary",
        )

        self.ai_next_button = QPushButton(
            "下一步"
        )

        self.ai_next_button.setProperty(
            "role",
            "primary",
        )

        back_button.clicked.connect(
            lambda checked=False: self._set_step(3)
        )

        self.ai_next_button.clicked.connect(
            lambda checked=False: self._set_step(4)
        )

        self.configure_ai_button = QPushButton(
            "管理员配置 AI"
        )

        self.configure_ai_button.setProperty(
            "role",
            "secondary",
        )

        self.configure_ai_button.clicked.connect(
            self._configure_ai
        )

        actions.addWidget(
            back_button
        )

        actions.addWidget(
            self.configure_ai_button
        )

        actions.addWidget(
            self.ai_next_button
        )

        self._refresh_ai_status()

        return page

    def _configure_ai(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if self._on_configure_ai is None:
            return

        self._on_configure_ai()

        self._refresh_ai_status()

    def _refresh_ai_status(
        self,
    ) -> None:
        try:
            configured = bool(
                self._is_ai_configured()
            )
        except Exception:
            configured = False

        if configured:
            self.ai_status_label.setText(
                "AI 服务已配置"
            )

            self.ai_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.success};"
            )

            self.ai_next_button.setEnabled(
                True
            )

        else:
            self.ai_status_label.setText(
                "AI 服务尚未配置"
            )

            self.ai_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.warning};"
            )

            self.ai_next_button.setEnabled(
                False
            )

    #
    # Step 4: WeCom
    #
    def _build_wecom_page(
        self,
    ) -> QWidget:
        page, layout = self._create_page(
            "连接企业微信通知",
            (
                "新询盘处理完成后，数字员工会通过企业微信发送内部提醒。"
            ),
        )

        self._add_field_label(
            layout,
            "企业微信群机器人 Webhook",
        )

        self.wecom_edit = QLineEdit()

        self.wecom_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.wecom_edit.setPlaceholderText(
            "粘贴 Webhook 地址"
        )

        layout.addWidget(
            self.wecom_edit
        )

        self.wecom_status_label = QLabel(
            "尚未测试连接"
        )

        self.wecom_status_label.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            self.wecom_status_label
        )

        actions = self._create_actions(
            layout
        )

        back_button = QPushButton(
            "上一步"
        )

        back_button.setProperty(
            "role",
            "secondary",
        )

        self.test_wecom_button = QPushButton(
            "测试通知"
        )

        self.test_wecom_button.setProperty(
            "role",
            "secondary",
        )

        self.wecom_next_button = QPushButton(
            "下一步"
        )

        self.wecom_next_button.setProperty(
            "role",
            "primary",
        )

        self.wecom_next_button.setEnabled(
            False
        )

        back_button.clicked.connect(
            lambda checked=False: self._set_step(2)
        )

        self.test_wecom_button.clicked.connect(
            self._test_wecom
        )

        self.wecom_next_button.clicked.connect(
            lambda checked=False: self._set_step(5)
        )

        actions.addWidget(
            back_button
        )

        actions.addWidget(
            self.test_wecom_button
        )

        actions.addWidget(
            self.wecom_next_button
        )

        return page

    def _test_wecom(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        webhook = (
            self.wecom_edit.text().strip()
        )

        try:
            success = bool(
                self._on_test_wecom(
                    webhook
                )
            )
        except Exception:
            success = False

        if success:
            self.wecom_status_label.setText(
                "企业微信已连接"
            )

            self.wecom_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.success};"
            )

            self.wecom_next_button.setEnabled(
                True
            )

        else:
            self.wecom_status_label.setText(
                "企业微信连接失败，请检查后重试"
            )

            self.wecom_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            self.wecom_next_button.setEnabled(
                False
            )

    #
    # Step 5: Administrator PIN
    #
    def _build_pin_page(
        self,
    ) -> QWidget:
        page, layout = self._create_page(
            "创建管理员 PIN",
            (
                "请设置 6 位数字 PIN。"
                "以后进入高级设置时需要使用这个 PIN。"
            ),
        )

        pin_hint = QLabel(
            (
                "PIN 不会以明文保存。"
                "系统只保存经过安全哈希处理后的验证信息。"
            )
        )

        pin_hint.setWordWrap(
            True
        )

        pin_hint.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            pin_hint
        )

        validator = (
            QRegularExpressionValidator(
                QRegularExpression(
                    r"[0-9]{0,6}"
                )
            )
        )

        self._add_field_label(
            layout,
            "管理员 PIN",
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

        layout.addWidget(
            self.pin_edit
        )

        self._add_field_label(
            layout,
            "确认 PIN",
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

        layout.addWidget(
            self.confirm_pin_edit
        )

        self.pin_status_label = QLabel(
            "请输入并确认 6 位数字 PIN"
        )

        self.pin_status_label.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            self.pin_status_label
        )

        actions = self._create_actions(
            layout
        )

        back_button = QPushButton(
            "上一步"
        )

        back_button.setProperty(
            "role",
            "secondary",
        )

        self.pin_next_button = QPushButton(
            "创建 PIN 并继续"
        )

        self.pin_next_button.setProperty(
            "role",
            "primary",
        )

        self.pin_next_button.setEnabled(
            False
        )

        back_button.clicked.connect(
            lambda checked=False: self._set_step(1)
        )

        self.pin_edit.textChanged.connect(
            self._refresh_pin_state
        )

        self.confirm_pin_edit.textChanged.connect(
            self._refresh_pin_state
        )

        self.pin_next_button.clicked.connect(
            self._create_pin
        )

        actions.addWidget(
            back_button
        )

        actions.addWidget(
            self.pin_next_button
        )

        return page

    def _refresh_pin_state(
        self,
        _text: str = "",
    ) -> None:
        pin = self.pin_edit.text()
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
            self.pin_status_label.setText(
                "两次输入的 PIN 不一致"
            )

            self.pin_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

        elif (
            pin_complete
            and confirmation_complete
            and pin == confirmation
        ):
            self.pin_status_label.setText(
                "PIN 可以创建"
            )

            self.pin_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.success};"
            )

        else:
            self.pin_status_label.setText(
                "请输入并确认 6 位数字 PIN"
            )

            self.pin_status_label.setStyleSheet(
                ""
            )

        self.pin_next_button.setEnabled(
            pin_complete
            and confirmation_complete
            and pin == confirmation
        )

    def _create_pin(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if not self.pin_next_button.isEnabled():
            return

        if self._on_create_pin is None:
            self.pin_status_label.setText(
                "管理员 PIN 服务尚未配置"
            )

            self.pin_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            return

        value = self.pin_edit.text()

        try:
            self._on_create_pin(
                value
            )

        except Exception:
            self.pin_status_label.setText(
                "PIN 创建失败，请重试"
            )

            self.pin_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            return

        self.pin_status_label.setText(
            "管理员 PIN 已创建"
        )

        self.pin_status_label.setStyleSheet(
            f"color: {LIGHT_TOKENS.success};"
        )

        self._refresh_ai_status()

        self._set_step(
            3
        )

    #
    # Step 6: History learning
    #
    def _build_history_page(
        self,
    ) -> QWidget:
        page, layout = self._create_page(
            "让数字员工学习你的历史邮件",
            (
                "数字员工会先学习你的回复习惯和客户上下文。"
                "这一步完成后才会开始自动处理新邮件。"
            ),
        )

        self.history_description = QLabel(
            (
                "历史邮件只用于学习，"
                "不会回复旧邮件，也不会发送任何邮件。"
            )
        )

        self.history_description.setWordWrap(
            True
        )

        self.history_description.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            self.history_description
        )

        safety_card = Card()

        safety_layout = QVBoxLayout(
            safety_card
        )

        safety_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        safety_layout.setSpacing(
            5
        )

        safety_title = QLabel(
            "安全说明"
        )

        safety_font = (
            safety_title.font()
        )

        safety_font.setBold(
            True
        )

        safety_title.setFont(
            safety_font
        )

        safety_text = QLabel(
            (
                "学习完成后会建立历史邮件 baseline。"
                "只有 baseline 建立成功，数字员工才会处理之后收到的新邮件。"
            )
        )

        safety_text.setWordWrap(
            True
        )

        safety_text.setProperty(
            "role",
            "muted",
        )

        safety_layout.addWidget(
            safety_title
        )

        safety_layout.addWidget(
            safety_text
        )

        layout.addWidget(
            safety_card
        )

        self.history_status_label = QLabel(
            "尚未开始学习"
        )

        self.history_status_label.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            self.history_status_label
        )

        actions = self._create_actions(
            layout
        )

        back_button = QPushButton(
            "上一步"
        )

        back_button.setProperty(
            "role",
            "secondary",
        )

        self.learn_history_button = QPushButton(
            "开始学习历史邮件"
        )

        self.learn_history_button.setProperty(
            "role",
            "secondary",
        )

        self.finish_button = QPushButton(
            "进入工作台"
        )

        self.finish_button.setProperty(
            "role",
            "primary",
        )

        #
        # Mandatory history-learning gate.
        #
        self.finish_button.setEnabled(
            False
        )

        back_button.clicked.connect(
            lambda checked=False: self._set_step(4)
        )

        self.learn_history_button.clicked.connect(
            self._learn_history
        )

        self.finish_button.clicked.connect(
            self._finish
        )

        actions.addWidget(
            back_button
        )

        actions.addWidget(
            self.learn_history_button
        )

        actions.addWidget(
            self.finish_button
        )

        return page

    def _learn_history(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        self.learn_history_button.setEnabled(
            False
        )

        self.finish_button.setEnabled(
            False
        )

        self.history_status_label.setText(
            "正在学习历史邮件…"
        )

        self.history_status_label.setStyleSheet(
            f"color: {LIGHT_TOKENS.primary};"
        )

        try:
            summary = (
                self._on_learn_history()
            )

        except Exception:
            self.history_status_label.setText(
                "历史学习失败，请重试"
            )

            self.history_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.danger};"
            )

            self.learn_history_button.setEnabled(
                True
            )

            return

        failed = int(
            getattr(
                summary,
                "failed",
                0,
            )
        )

        if failed > 0:
            self.history_status_label.setText(
                "历史学习未完成，请重试"
            )

            self.history_status_label.setStyleSheet(
                f"color: {LIGHT_TOKENS.warning};"
            )

            self.learn_history_button.setEnabled(
                True
            )

            return

        self.history_status_label.setText(
            "历史学习已完成"
        )

        self.history_status_label.setStyleSheet(
            f"color: {LIGHT_TOKENS.success};"
        )

        self.finish_button.setEnabled(
            True
        )

    def _finish(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if not self.finish_button.isEnabled():
            return

        self._on_complete()
