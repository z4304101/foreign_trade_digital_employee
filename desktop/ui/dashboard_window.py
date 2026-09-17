from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.health import AppStatus
from desktop.models import DashboardSnapshot
from desktop.ui.components import (
    Card,
    SectionTitle,
    StatCard,
    StatusChip,
)


class DashboardWindow(QMainWindow):
    """
    Fluent-style operational dashboard.

    Only operational summaries are displayed.

    The dashboard never displays:
    - complete customer email bodies
    - mailbox authorization codes
    - AI API keys
    - WeCom webhook secrets

    Desktop V1 remains draft-only.
    """

    def __init__(
        self,
        *,
        on_pause: Callable[[], None] | None = None,
        on_resume: Callable[[], None] | None = None,
        on_run_now: Callable[[], None] | None = None,
        on_settings: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()

        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_run_now = on_run_now
        self._on_settings = on_settings

        self._close_to_tray_enabled = False

        self._current_status = (
            AppStatus.WAITING_INITIALIZATION
        )

        self.setWindowTitle(
            "外贸数字员工"
        )

        self.resize(
            1040,
            760,
        )

        self.setMinimumSize(
            900,
            680,
        )

        central_widget = QWidget(self)

        central_widget.setObjectName(
            "AppRoot"
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            30,
            26,
            30,
            26,
        )

        main_layout.setSpacing(
            18
        )

        #
        # Header
        #
        header_layout = QHBoxLayout()

        header_layout.setSpacing(
            16
        )

        title_layout = QVBoxLayout()

        title_layout.setSpacing(
            2
        )

        title_label = QLabel(
            "外贸数字员工"
        )

        title_font = title_label.font()

        title_font.setPointSize(
            22
        )

        title_font.setBold(
            True
        )

        title_label.setFont(
            title_font
        )

        subtitle_label = QLabel(
            "AI Foreign Trade Assistant"
        )

        subtitle_label.setProperty(
            "role",
            "muted",
        )

        title_layout.addWidget(
            title_label
        )

        title_layout.addWidget(
            subtitle_label
        )

        header_layout.addLayout(
            title_layout
        )

        header_layout.addStretch(
            1
        )

        #
        # Keep status_label as a stable public attribute
        # for controller/tests, while status_chip is the
        # actual visible Fluent status control.
        #
        self.status_label = QLabel(
            "等待初始化"
        )

        self.status_label.setVisible(
            False
        )

        self.status_chip = StatusChip(
            "等待初始化",
            "neutral",
        )

        header_layout.addWidget(
            self.status_chip,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )

        self.settings_button = QPushButton(
            "设置"
        )

        self.settings_button.setProperty(
            "role",
            "secondary",
        )

        self.settings_button.setFixedWidth(
            82
        )

        self.settings_button.clicked.connect(
            self._handle_settings_clicked
        )

        header_layout.addWidget(
            self.settings_button
        )

        main_layout.addLayout(
            header_layout
        )

        #
        # Today overview
        #
        main_layout.addWidget(
            SectionTitle(
                "今日概览"
            )
        )

        summary_layout = QHBoxLayout()

        summary_layout.setSpacing(
            14
        )

        self.scanned_card = StatCard(
            "今日扫描",
            "邮件",
        )

        self.inquiries_card = StatCard(
            "新询盘",
            "待查看",
        )

        self.drafts_card = StatCard(
            "已生成草稿",
            "163 草稿箱",
        )

        summary_layout.addWidget(
            self.scanned_card,
            1,
        )

        summary_layout.addWidget(
            self.inquiries_card,
            1,
        )

        summary_layout.addWidget(
            self.drafts_card,
            1,
        )

        main_layout.addLayout(
            summary_layout
        )

        #
        # Service + polling row
        #
        info_layout = QHBoxLayout()

        info_layout.setSpacing(
            14
        )

        service_card = Card()

        service_layout = QVBoxLayout(
            service_card
        )

        service_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        service_layout.setSpacing(
            10
        )

        service_layout.addWidget(
            SectionTitle(
                "服务状态"
            )
        )

        mail_row = QHBoxLayout()

        mail_row.addWidget(
            QLabel("邮箱服务")
        )

        mail_row.addStretch(1)

        self.mail_service_label = QLabel(
            "等待配置"
        )

        self.mail_service_label.setProperty(
            "role",
            "muted",
        )

        mail_row.addWidget(
            self.mail_service_label
        )

        service_layout.addLayout(
            mail_row
        )

        ai_row = QHBoxLayout()

        ai_row.addWidget(
            QLabel("AI 服务")
        )

        ai_row.addStretch(1)

        self.ai_service_label = QLabel(
            "等待配置"
        )

        self.ai_service_label.setProperty(
            "role",
            "muted",
        )

        ai_row.addWidget(
            self.ai_service_label
        )

        service_layout.addLayout(
            ai_row
        )

        wecom_row = QHBoxLayout()

        wecom_row.addWidget(
            QLabel("企业微信")
        )

        wecom_row.addStretch(1)

        self.wecom_label = QLabel(
            "未连接"
        )

        self.wecom_label.setProperty(
            "role",
            "muted",
        )

        wecom_row.addWidget(
            self.wecom_label
        )

        service_layout.addLayout(
            wecom_row
        )

        info_layout.addWidget(
            service_card,
            1,
        )

        polling_card = Card()

        polling_layout = QVBoxLayout(
            polling_card
        )

        polling_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        polling_layout.setSpacing(
            10
        )

        polling_layout.addWidget(
            SectionTitle(
                "自动检查"
            )
        )

        self.last_check_label = QLabel(
            "上次：--"
        )

        self.next_check_label = QLabel(
            "下次：--"
        )

        self.last_check_label.setProperty(
            "role",
            "muted",
        )

        self.next_check_label.setProperty(
            "role",
            "muted",
        )

        polling_layout.addWidget(
            self.last_check_label
        )

        polling_layout.addWidget(
            self.next_check_label
        )

        polling_layout.addStretch(
            1
        )

        info_layout.addWidget(
            polling_card,
            1,
        )

        learning_card = Card()

        learning_layout = QVBoxLayout(
            learning_card
        )

        learning_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        learning_layout.setSpacing(
            10
        )

        learning_layout.addWidget(
            SectionTitle(
                "学习状态"
            )
        )

        history_row = QHBoxLayout()

        history_row.addWidget(
            QLabel("历史邮件")
        )

        history_row.addStretch(1)

        self.history_label = QLabel(
            "未完成"
        )

        self.history_label.setProperty(
            "role",
            "muted",
        )

        history_row.addWidget(
            self.history_label
        )

        learning_layout.addLayout(
            history_row
        )

        style_row = QHBoxLayout()

        style_row.addWidget(
            QLabel("回复风格")
        )

        style_row.addStretch(1)

        self.style_label = QLabel(
            "未学习"
        )

        self.style_label.setProperty(
            "role",
            "muted",
        )

        style_row.addWidget(
            self.style_label
        )

        learning_layout.addLayout(
            style_row
        )

        learning_layout.addStretch(
            1
        )

        info_layout.addWidget(
            learning_card,
            1,
        )

        main_layout.addLayout(
            info_layout
        )

        #
        # Recent processing
        #
        recent_header = QHBoxLayout()

        recent_header.addWidget(
            SectionTitle(
                "最近处理"
            )
        )

        recent_header.addStretch(
            1
        )

        recent_hint = QLabel(
            "最近 10 条"
        )

        recent_hint.setProperty(
            "role",
            "muted",
        )

        recent_header.addWidget(
            recent_hint
        )

        main_layout.addLayout(
            recent_header
        )

        recent_card = Card()

        recent_layout = QVBoxLayout(
            recent_card
        )

        recent_layout.setContentsMargins(
            1,
            1,
            1,
            1,
        )

        self.recent_table = QTableWidget(
            0,
            4,
        )

        self.recent_table.setHorizontalHeaderLabels(
            [
                "客户",
                "主题",
                "处理时间",
                "状态",
            ]
        )

        self.recent_table.verticalHeader().setVisible(
            False
        )

        self.recent_table.verticalHeader().setDefaultSectionSize(
            44
        )

        self.recent_table.setShowGrid(
            False
        )

        self.recent_table.setAlternatingRowColors(
            False
        )

        self.recent_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )

        self.recent_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.recent_table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        self.recent_table.setFrameShape(
            QFrame.Shape.NoFrame
        )

        header = (
            self.recent_table.horizontalHeader()
        )

        header.setStretchLastSection(
            True
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch,
        )

        self.recent_table.setMaximumHeight(
            250
        )

        recent_layout.addWidget(
            self.recent_table
        )

        main_layout.addWidget(
            recent_card
        )

        #
        # Bottom actions
        #
        actions_layout = QHBoxLayout()

        actions_layout.addStretch(
            1
        )

        self.pause_button = QPushButton(
            "暂停工作"
        )

        self.pause_button.setProperty(
            "role",
            "secondary",
        )

        self.run_now_button = QPushButton(
            "立即检查邮件"
        )

        self.run_now_button.setProperty(
            "role",
            "primary",
        )

        self.pause_button.clicked.connect(
            self._handle_pause_resume_clicked
        )

        self.run_now_button.clicked.connect(
            self._handle_run_now_clicked
        )

        actions_layout.addWidget(
            self.pause_button
        )

        actions_layout.addWidget(
            self.run_now_button
        )

        main_layout.addLayout(
            actions_layout
        )

        self.setCentralWidget(
            central_widget
        )

    def set_close_to_tray(
        self,
        enabled: bool = True,
    ) -> None:
        self._close_to_tray_enabled = bool(
            enabled
        )

    def closeEvent(
        self,
        event,
    ) -> None:
        if self._close_to_tray_enabled:
            event.ignore()
            self.hide()
            return

        super().closeEvent(
            event
        )

    def _handle_pause_resume_clicked(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if (
            self._current_status
            == AppStatus.PAUSED
        ):
            if self._on_resume is not None:
                self._on_resume()

            return

        if self._on_pause is not None:
            self._on_pause()

    def _handle_run_now_clicked(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if self._on_run_now is not None:
            self._on_run_now()

    def _handle_settings_clicked(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if self._on_settings is not None:
            self._on_settings()

    def render(
        self,
        snapshot: DashboardSnapshot,
    ) -> None:
        self._current_status = (
            snapshot.status
        )

        status_visual = {
            AppStatus.WAITING_INITIALIZATION: (
                "等待初始化",
                "neutral",
            ),
            AppStatus.RUNNING: (
                "正在运行",
                "success",
            ),
            AppStatus.PAUSED: (
                "已暂停",
                "neutral",
            ),
            AppStatus.NEEDS_ATTENTION: (
                "需要处理",
                "warning",
            ),
            AppStatus.SERVICE_ERROR: (
                "服务异常",
                "danger",
            ),
        }

        status_text, tone = (
            status_visual.get(
                snapshot.status,
                (
                    "未知状态",
                    "neutral",
                ),
            )
        )

        self.status_label.setText(
            status_text
        )

        self.status_chip.set_status(
            status_text,
            tone,
        )

        work_actions_enabled = (
            snapshot.status
            not in {
                AppStatus.WAITING_INITIALIZATION,
                AppStatus.SERVICE_ERROR,
            }
        )

        self.pause_button.setEnabled(
            work_actions_enabled
        )

        self.run_now_button.setEnabled(
            work_actions_enabled
        )

        self.settings_button.setEnabled(
            True
        )

        if (
            snapshot.status
            == AppStatus.PAUSED
        ):
            self.pause_button.setText(
                "继续工作"
            )
        else:
            self.pause_button.setText(
                "暂停工作"
            )

        self.last_check_label.setText(
            "上次："
            + (
                snapshot.last_check_at
                or "--"
            )
        )

        self.next_check_label.setText(
            "下次："
            + (
                snapshot.next_check_at
                or "--"
            )
        )

        self.scanned_card.set_value(
            str(
                snapshot.today_scanned
            )
        )

        self.inquiries_card.set_value(
            str(
                snapshot.today_new_inquiries
            )
        )

        self.drafts_card.set_value(
            str(
                snapshot.today_drafts
            )
        )

        self.history_label.setText(
            (
                "已完成"
                if snapshot.history_ready
                else "未完成"
            )
        )

        self.style_label.setText(
            (
                "已学习"
                if snapshot.style_ready
                else "未学习"
            )
        )

        self.wecom_label.setText(
            (
                "已连接"
                if snapshot.wecom_connected
                else "未连接"
            )
        )

        if snapshot.status in {
            AppStatus.RUNNING,
            AppStatus.PAUSED,
        }:
            service_text = "正常"

        elif (
            snapshot.status
            == AppStatus.NEEDS_ATTENTION
        ):
            service_text = "需要关注"

        elif (
            snapshot.status
            == AppStatus.SERVICE_ERROR
        ):
            service_text = "需要检查"

        else:
            service_text = "等待配置"

        self.mail_service_label.setText(
            service_text
        )

        self.ai_service_label.setText(
            service_text
        )

        records = tuple(
            snapshot.recent_records
        )[:10]

        self.recent_table.setRowCount(
            len(records)
        )

        for row_index, record in enumerate(
            records
        ):
            self.recent_table.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    record.sender
                ),
            )

            self.recent_table.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    record.subject
                ),
            )

            self.recent_table.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    record.processed_at
                ),
            )

            status_parts = []

            if record.analysis_completed:
                status_parts.append(
                    "已分析"
                )

            if record.draft_saved:
                status_parts.append(
                    "草稿已生成"
                )

            if record.wecom_notified:
                status_parts.append(
                    "企微已通知"
                )

            status_summary = (
                " · ".join(
                    status_parts
                )
                if status_parts
                else "未完成"
            )

            self.recent_table.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    status_summary
                ),
            )
