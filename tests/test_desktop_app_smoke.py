import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from desktop.health import AppStatus
from desktop.models import DashboardSnapshot
from desktop.ui.dashboard_window import DashboardWindow


def test_dashboard_renders_running_snapshot():
    app = (
        QApplication.instance()
        or QApplication([])
    )

    window = DashboardWindow()

    window.render(
        DashboardSnapshot(
            status=AppStatus.RUNNING,
        )
    )

    assert window.status_label.text() == "正在运行"
    assert (
        window.status_chip.text_label.text()
        == "正在运行"
    )
    assert window.recent_table.rowCount() <= 10

    window.close()


def test_dashboard_renders_fluent_operational_summary():
    from desktop.models import ProcessRecord

    app = (
        QApplication.instance()
        or QApplication([])
    )

    window = DashboardWindow()

    window.render(
        DashboardSnapshot(
            status=AppStatus.RUNNING,
            last_check_at="刚刚",
            next_check_at="2 分 48 秒后",
            today_scanned=12,
            today_new_inquiries=2,
            today_drafts=2,
            history_ready=True,
            style_ready=True,
            wecom_connected=True,
            recent_records=(
                ProcessRecord(
                    sender="buyer@example.com",
                    subject="Inquiry for MA310E",
                    processed_at="刚刚",
                    analysis_completed=True,
                    draft_saved=True,
                    wecom_notified=True,
                ),
            ),
        )
    )

    assert (
        window.status_chip.text_label.text()
        == "正在运行"
    )

    assert (
        window.scanned_card.value_label.text()
        == "12"
    )

    assert (
        window.inquiries_card.value_label.text()
        == "2"
    )

    assert (
        window.drafts_card.value_label.text()
        == "2"
    )

    assert (
        window.last_check_label.text()
        == "上次：刚刚"
    )

    assert (
        window.next_check_label.text()
        == "下次：2 分 48 秒后"
    )

    assert (
        window.history_label.text()
        == "已完成"
    )

    assert (
        window.style_label.text()
        == "已学习"
    )

    assert (
        window.wecom_label.text()
        == "已连接"
    )

    assert window.recent_table.rowCount() == 1

    assert (
        window.recent_table.item(
            0,
            0,
        ).text()
        == "buyer@example.com"
    )

    assert (
        window.recent_table.item(
            0,
            1,
        ).text()
        == "Inquiry for MA310E"
    )

    window.close()


def test_dashboard_exposes_safe_user_actions():
    from PySide6.QtWidgets import QPushButton

    app = (
        QApplication.instance()
        or QApplication([])
    )

    calls = []

    window = DashboardWindow(
        on_pause=lambda: calls.append("pause"),
        on_run_now=lambda: calls.append("run_now"),
        on_settings=lambda: calls.append("settings"),
    )

    assert window.pause_button.text() == "暂停工作"
    assert window.run_now_button.text() == "立即检查邮件"
    assert window.settings_button.text() == "设置"

    window.pause_button.click()
    window.run_now_button.click()
    window.settings_button.click()

    assert calls == [
        "pause",
        "run_now",
        "settings",
    ]

    # Desktop V1 remains draft-only.
    # The dashboard must never expose an email-send action.
    button_texts = [
        button.text()
        for button in window.findChildren(QPushButton)
    ]

    assert "发送邮件" not in button_texts
    assert "发送" not in button_texts

    window.close()


def test_dashboard_pause_button_switches_between_pause_and_resume():
    app = (
        QApplication.instance()
        or QApplication([])
    )

    calls = []

    window = DashboardWindow(
        on_pause=lambda: calls.append("pause"),
        on_resume=lambda: calls.append("resume"),
    )

    #
    # Running state
    #
    window.render(
        DashboardSnapshot(
            status=AppStatus.RUNNING,
        )
    )

    assert (
        window.pause_button.text()
        == "暂停工作"
    )

    window.pause_button.click()

    assert calls == [
        "pause",
    ]

    #
    # Paused state
    #
    window.render(
        DashboardSnapshot(
            status=AppStatus.PAUSED,
        )
    )

    assert (
        window.pause_button.text()
        == "继续工作"
    )

    window.pause_button.click()

    assert calls == [
        "pause",
        "resume",
    ]

    window.close()


def test_dashboard_disables_work_actions_when_not_operational():
    app = (
        QApplication.instance()
        or QApplication([])
    )

    window = DashboardWindow()

    #
    # Not initialized yet:
    # no mail-processing action should be available.
    #
    window.render(
        DashboardSnapshot(
            status=AppStatus.WAITING_INITIALIZATION,
        )
    )

    assert window.pause_button.isEnabled() is False
    assert window.run_now_button.isEnabled() is False
    assert window.settings_button.isEnabled() is True

    #
    # Hard service failure:
    # user should fix settings instead of forcing processing.
    #
    window.render(
        DashboardSnapshot(
            status=AppStatus.SERVICE_ERROR,
        )
    )

    assert window.pause_button.isEnabled() is False
    assert window.run_now_button.isEnabled() is False
    assert window.settings_button.isEnabled() is True

    #
    # Needs attention is degraded, but still operational.
    #
    window.render(
        DashboardSnapshot(
            status=AppStatus.NEEDS_ATTENTION,
        )
    )

    assert window.pause_button.isEnabled() is True
    assert window.run_now_button.isEnabled() is True
    assert window.settings_button.isEnabled() is True

    #
    # Normal running state.
    #
    window.render(
        DashboardSnapshot(
            status=AppStatus.RUNNING,
        )
    )

    assert window.pause_button.isEnabled() is True
    assert window.run_now_button.isEnabled() is True
    assert window.settings_button.isEnabled() is True

    window.close()


def test_desktop_application_does_not_start_scheduler_before_production_gate():
    from desktop.app import DesktopApplication

    class FakeWindow:
        def __init__(self):
            self.show_calls = 0

        def show(self):
            self.show_calls += 1

    class FakeScheduler:
        def __init__(self):
            self.start_calls = 0

        def start(self):
            self.start_calls += 1
            return True

    window = FakeWindow()
    scheduler = FakeScheduler()

    desktop = DesktopApplication(
        window=window,
        scheduler=scheduler,
        ready_check=lambda: False,
    )

    desktop.show()

    # The desktop shell itself may open.
    assert window.show_calls == 1

    # But production mail processing must remain closed.
    assert scheduler.start_calls == 0


def test_desktop_application_starts_scheduler_after_production_gate():
    from desktop.app import DesktopApplication

    class FakeWindow:
        def __init__(self):
            self.show_calls = 0

        def show(self):
            self.show_calls += 1

    class FakeScheduler:
        def __init__(self):
            self.start_calls = 0

        def start(self):
            self.start_calls += 1
            return True

    window = FakeWindow()
    scheduler = FakeScheduler()

    desktop = DesktopApplication(
        window=window,
        scheduler=scheduler,
        ready_check=lambda: True,
    )

    desktop.show()

    assert window.show_calls == 1
    assert scheduler.start_calls == 1


def test_desktop_application_controls_scheduler():
    from desktop.app import DesktopApplication

    class FakeWindow:
        def show(self):
            pass

    class FakeScheduler:
        def __init__(self):
            self.calls = []

        def start(self):
            self.calls.append("start")
            return True

        def pause(self):
            self.calls.append("pause")

        def resume(self):
            self.calls.append("resume")

        def run_now(self):
            self.calls.append("run_now")
            return {
                "total": 0,
                "processed": 0,
                "skipped": 0,
                "failed": 0,
            }

    scheduler = FakeScheduler()

    desktop = DesktopApplication(
        window=FakeWindow(),
        scheduler=scheduler,
        ready_check=lambda: True,
    )

    desktop.pause()
    desktop.resume()
    result = desktop.run_now()

    assert scheduler.calls == [
        "pause",
        "resume",
        "run_now",
    ]

    assert result == {
        "total": 0,
        "processed": 0,
        "skipped": 0,
        "failed": 0,
    }



def test_onboarding_window_requires_history_before_completion():
    from desktop.ui.onboarding_window import OnboardingWindow

    app = (
        QApplication.instance()
        or QApplication([])
    )

    calls = []

    class Summary:
        failed = 0

    window = OnboardingWindow(
        on_test_mail=lambda email, auth: True,
        on_save_identity=lambda name, title, company: (
            calls.append(
                (
                    "identity",
                    name,
                    title,
                    company,
                )
            )
        ),
        is_ai_configured=lambda: True,
        on_test_wecom=lambda webhook: True,
        on_learn_history=lambda: Summary(),
        on_complete=lambda: calls.append(
            ("complete",)
        ),
    )

    assert window.stack.currentIndex() == 0

    #
    # History learning is a hard gate.
    #
    assert window.finish_button.isEnabled() is False

    #
    # Step 1: mailbox
    #
    window.email_edit.setText(
        "sales@163.com"
    )

    window.auth_code_edit.setText(
        "secret"
    )

    window.test_mail_button.click()

    assert (
        window.email_status_label.text()
        == "邮箱连接正常"
    )

    assert (
        window.email_next_button.isEnabled()
        is True
    )

    window.email_next_button.click()

    assert window.stack.currentIndex() == 1

    #
    # Step 2: identity
    #
    window.name_edit.setText(
        "Alice"
    )

    window.title_edit.setText(
        "Sales Manager"
    )

    window.company_edit.setText(
        "Example Co."
    )

    window.identity_next_button.click()

    assert window.stack.currentIndex() == 2

    #
    # Step 3: AI
    #
    assert (
        window.ai_status_label.text()
        == "AI 服务已配置"
    )

    assert (
        window.ai_next_button.isEnabled()
        is True
    )

    window.ai_next_button.click()

    assert window.stack.currentIndex() == 3

    #
    # Step 4: WeCom
    #
    window.wecom_edit.setText(
        "https://example.invalid/hook"
    )

    window.test_wecom_button.click()

    assert (
        window.wecom_status_label.text()
        == "企业微信已连接"
    )

    assert (
        window.wecom_next_button.isEnabled()
        is True
    )

    window.wecom_next_button.click()

    assert window.stack.currentIndex() == 4

    #
    # Step 5: history learning
    #
    description = (
        window.history_description.text()
    )

    assert "历史邮件只用于学习" in description
    assert "1000" not in description
    assert "6 months" not in description

    assert (
        window.finish_button.isEnabled()
        is False
    )

    window.learn_history_button.click()

    assert (
        window.history_status_label.text()
        == "历史学习已完成"
    )

    assert (
        window.finish_button.isEnabled()
        is True
    )

    window.finish_button.click()

    assert calls[-1] == (
        "complete",
    )

    window.close()


def test_onboarding_history_failure_keeps_finish_locked():
    from desktop.ui.onboarding_window import OnboardingWindow

    app = (
        QApplication.instance()
        or QApplication([])
    )

    class Summary:
        failed = 1

    window = OnboardingWindow(
        on_test_mail=lambda email, auth: True,
        on_save_identity=lambda name, title, company: None,
        is_ai_configured=lambda: True,
        on_test_wecom=lambda webhook: True,
        on_learn_history=lambda: Summary(),
        on_complete=lambda: None,
    )

    window.stack.setCurrentIndex(4)

    window.learn_history_button.click()

    assert (
        window.finish_button.isEnabled()
        is False
    )

    assert (
        window.learn_history_button.isEnabled()
        is True
    )

    assert (
        window.history_status_label.text()
        == "历史学习未完成，请重试"
    )

    window.close()
