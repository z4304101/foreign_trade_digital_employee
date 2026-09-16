from collections.abc import Callable

from PySide6.QtWidgets import (
    QGroupBox,
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


class DashboardWindow(QMainWindow):
    """
    Main dashboard window for the desktop application.

    The dashboard only displays operational summaries.

    It never displays:
    - customer email bodies
    - mailbox auth codes
    - API keys
    - WeCom webhook secrets

    Desktop V1 remains draft-only and does not expose
    any email-send action.
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

        self._current_status = (
            AppStatus.WAITING_INITIALIZATION
        )

        self.setWindowTitle(
            "外贸数字员工"
        )

        self.resize(
            900,
            680,
        )

        central_widget = QWidget(self)

        main_layout = QVBoxLayout(
            central_widget
        )

        #
        # Application status
        #
        self.status_label = QLabel(
            "等待初始化"
        )

        main_layout.addWidget(
            self.status_label
        )

        #
        # Polling status
        #
        check_group = QGroupBox(
            "邮件检查"
        )

        check_layout = QVBoxLayout(
            check_group
        )

        self.last_check_label = QLabel(
            "上次检查：--"
        )

        self.next_check_label = QLabel(
            "下次检查：--"
        )

        check_layout.addWidget(
            self.last_check_label
        )

        check_layout.addWidget(
            self.next_check_label
        )

        main_layout.addWidget(
            check_group
        )

        #
        # Today's summary
        #
        summary_group = QGroupBox(
            "今日统计"
        )

        summary_layout = QHBoxLayout(
            summary_group
        )

        self.scanned_label = QLabel(
            "今日扫描：0"
        )

        self.inquiries_label = QLabel(
            "新询盘：0"
        )

        self.drafts_label = QLabel(
            "已生成草稿：0"
        )

        summary_layout.addWidget(
            self.scanned_label
        )

        summary_layout.addWidget(
            self.inquiries_label
        )

        summary_layout.addWidget(
            self.drafts_label
        )

        main_layout.addWidget(
            summary_group
        )

        #
        # Learning / integration state
        #
        readiness_group = QGroupBox(
            "数字员工状态"
        )

        readiness_layout = QVBoxLayout(
            readiness_group
        )

        self.history_label = QLabel(
            "历史学习：未完成"
        )

        self.style_label = QLabel(
            "回复风格：未学习"
        )

        self.wecom_label = QLabel(
            "企业微信：未连接"
        )

        readiness_layout.addWidget(
            self.history_label
        )

        readiness_layout.addWidget(
            self.style_label
        )

        readiness_layout.addWidget(
            self.wecom_label
        )

        main_layout.addWidget(
            readiness_group
        )

        #
        # Recent processing records
        #
        recent_group = QGroupBox(
            "最近处理"
        )

        recent_layout = QVBoxLayout(
            recent_group
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

        recent_layout.addWidget(
            self.recent_table
        )

        main_layout.addWidget(
            recent_group
        )

        #
        # Safe user actions
        #
        actions_layout = QHBoxLayout()

        self.pause_button = QPushButton(
            "暂停工作"
        )

        self.run_now_button = QPushButton(
            "立即检查一次"
        )

        self.settings_button = QPushButton(
            "设置"
        )

        self.pause_button.clicked.connect(
            self._handle_pause_resume_clicked
        )

        self.run_now_button.clicked.connect(
            self._handle_run_now_clicked
        )

        self.settings_button.clicked.connect(
            self._handle_settings_clicked
        )

        actions_layout.addWidget(
            self.pause_button
        )

        actions_layout.addWidget(
            self.run_now_button
        )

        actions_layout.addWidget(
            self.settings_button
        )

        main_layout.addLayout(
            actions_layout
        )

        self.setCentralWidget(
            central_widget
        )

    def _handle_pause_resume_clicked(
        self,
        checked: bool = False,
    ) -> None:
        del checked

        if self._current_status == AppStatus.PAUSED:
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
        """
        Render one dashboard state snapshot.
        """

        self._current_status = snapshot.status

        status_text = {
            AppStatus.WAITING_INITIALIZATION: "等待初始化",
            AppStatus.RUNNING: "正在运行",
            AppStatus.PAUSED: "已暂停",
            AppStatus.NEEDS_ATTENTION: "需要注意",
            AppStatus.SERVICE_ERROR: "服务异常",
        }

        self.status_label.setText(
            status_text.get(
                snapshot.status,
                "未知状态",
            )
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

        if snapshot.status == AppStatus.PAUSED:
            self.pause_button.setText(
                "继续工作"
            )
        else:
            self.pause_button.setText(
                "暂停工作"
            )

        self.last_check_label.setText(
            "上次检查："
            + (
                snapshot.last_check_at
                or "--"
            )
        )

        self.next_check_label.setText(
            "下次检查："
            + (
                snapshot.next_check_at
                or "--"
            )
        )

        self.scanned_label.setText(
            f"今日扫描：{snapshot.today_scanned}"
        )

        self.inquiries_label.setText(
            f"新询盘：{snapshot.today_new_inquiries}"
        )

        self.drafts_label.setText(
            f"已生成草稿：{snapshot.today_drafts}"
        )

        self.history_label.setText(
            (
                "历史学习：✅ 已完成"
                if snapshot.history_ready
                else "历史学习：未完成"
            )
        )

        self.style_label.setText(
            (
                "回复风格：✅ 已学习"
                if snapshot.style_ready
                else "回复风格：未学习"
            )
        )

        self.wecom_label.setText(
            (
                "企业微信：✅ 已连接"
                if snapshot.wecom_connected
                else "企业微信：未连接"
            )
        )

        records = tuple(
            snapshot.recent_records
        )[:10]

        self.recent_table.setRowCount(
            len(records)
        )

        for row_index, record in enumerate(records):
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
                    "草稿已保存"
                )

            if record.wecom_notified:
                status_parts.append(
                    "企微已通知"
                )

            status_summary = (
                " / ".join(status_parts)
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
