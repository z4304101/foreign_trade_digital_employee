# Desktop V1 Fluent UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把当前已经可运行的 PySide6 QWidget 桌面壳升级为商务高级浅色 Fluent 风，并完成首次向导、普通设置和首次运行页面切换，同时不改动邮件业务核心和“只生成草稿、不自动发送”的安全边界。

**Architecture:** 保留现有 PySide6 QWidget、`DashboardWindow`、`DesktopApplication`、Scheduler、OnboardingService 和业务核心；新增轻量 `theme.py` + `components.py` 作为统一 Design System。Dashboard、Onboarding、Settings 只消费现有状态模型和回调，不复制邮箱、AI、历史学习、企业微信业务逻辑。

**Tech Stack:** Python 3、PySide6 QWidget/QSS、pytest、现有 `desktop.models` / `desktop.health` / `desktop.scheduler` / `desktop.onboarding`。

**Spec:** `docs/superpowers/specs/2026-09-17-desktop-v1-fluent-ui-design.md`

## Global Constraints

- V1 只实现高质量浅色模式，不做深色模式。
- 视觉方向为商务高级浅色 Fluent 风 + macOS 极简克制感。
- 继续使用 QWidget，不迁移到 QML。
- 不直接依赖第三方 Fluent 商业组件库。
- macOS 与 Windows 共用同一套 UI 业务源码。
- Dashboard 不显示完整客户邮件正文、邮箱授权码、API Key、Webhook。
- Desktop V1 不提供任何“发送客户邮件”按钮。
- Fresh Install 必须完成历史学习并建立 processed baseline 后才能进入正式运行。
- 普通用户不显示 API Key、Base URL、IMAP Host/Port、history months/limit、日志级别。
- 管理员 PIN 的安全哈希/存储继续由原 Desktop V1 Task 10 实现；本计划只提供管理员入口 UI 和回调接口，不重复实现 PIN 密码学逻辑。
- 所有行为变更继续执行 RED -> GREEN -> focused regression -> full regression。
- 不删除、跳过或弱化现有安全测试。

---

## File Structure

本计划新增/修改：

```text
desktop/ui/
├── theme.py                 # 浅色 Fluent token + 全局 QSS
├── components.py            # Card / StatCard / StatusChip / SectionTitle
├── dashboard_window.py      # 现代化 Dashboard，保留现有回调接口
├── onboarding_window.py     # 5 步首次向导，历史学习必做
└── settings_dialog.py       # 普通设置 + 管理员入口

desktop/app.py               # 首次向导 / Dashboard 顶层页面切换

tests/
├── test_desktop_theme.py
└── test_desktop_app_smoke.py
```

不在本计划修改：

```text
mail_reader/
mail_writer/
agent/
history_learning/     # 只通过 OnboardingService 调用
wecom/
desktop/core_bridge.py
desktop/scheduler.py
```

---

### Task 1: 建立浅色 Fluent Design System

**Files:**
- Create: `desktop/ui/theme.py`
- Create: `desktop/ui/components.py`
- Create: `tests/test_desktop_theme.py`

**Interfaces:**
- Produces: `ThemeTokens`
- Produces: `LIGHT_TOKENS: ThemeTokens`
- Produces: `build_light_stylesheet(tokens: ThemeTokens = LIGHT_TOKENS) -> str`
- Produces: `apply_light_theme(app: QApplication) -> None`
- Produces: `Card(QWidget)`
- Produces: `SectionTitle(QLabel)`
- Produces: `StatCard(QWidget).set_value(value: str) -> None`
- Produces: `StatusChip(QWidget).set_status(text: str, tone: str) -> None`

- [ ] **Step 1: 写 Theme token 与 QSS RED 测试**

```python
from desktop.ui.theme import (
    LIGHT_TOKENS,
    build_light_stylesheet,
)


def test_light_theme_exposes_required_fluent_tokens():
    assert LIGHT_TOKENS.app_background == "#F5F7FA"
    assert LIGHT_TOKENS.surface == "#FFFFFF"
    assert LIGHT_TOKENS.primary == "#2563EB"
    assert LIGHT_TOKENS.success == "#16A34A"
    assert LIGHT_TOKENS.warning == "#D97706"
    assert LIGHT_TOKENS.danger == "#DC2626"
    assert LIGHT_TOKENS.radius_card == 14


def test_light_stylesheet_targets_named_fluent_roles():
    qss = build_light_stylesheet()
    assert '#AppRoot' in qss
    assert 'QPushButton[role="primary"]' in qss
    assert 'QPushButton[role="secondary"]' in qss
    assert 'QFrame[role="card"]' in qss
    assert 'QLineEdit' in qss
```

- [ ] **Step 2: 运行 RED**

Run:

```bash
python -m pytest tests/test_desktop_theme.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'desktop.ui.theme'`.

- [ ] **Step 3: 实现 `theme.py`**

```python
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class ThemeTokens:
    app_background: str
    surface: str
    surface_muted: str
    border: str
    text_primary: str
    text_secondary: str
    primary: str
    primary_hover: str
    success: str
    warning: str
    danger: str
    radius_card: int = 14
    radius_control: int = 10


LIGHT_TOKENS = ThemeTokens(
    app_background="#F5F7FA",
    surface="#FFFFFF",
    surface_muted="#F8FAFC",
    border="#E5E7EB",
    text_primary="#111827",
    text_secondary="#6B7280",
    primary="#2563EB",
    primary_hover="#1D4ED8",
    success="#16A34A",
    warning="#D97706",
    danger="#DC2626",
)


def build_light_stylesheet(
    tokens: ThemeTokens = LIGHT_TOKENS,
) -> str:
    return f"""
    QWidget#AppRoot {{
        background: {tokens.app_background};
        color: {tokens.text_primary};
    }}
    QFrame[role="card"] {{
        background: {tokens.surface};
        border: 1px solid {tokens.border};
        border-radius: {tokens.radius_card}px;
    }}
    QLabel[role="muted"] {{
        color: {tokens.text_secondary};
    }}
    QPushButton {{
        min-height: 36px;
        padding: 0 16px;
        border-radius: {tokens.radius_control}px;
        font-weight: 600;
    }}
    QPushButton[role="primary"] {{
        color: white;
        background: {tokens.primary};
        border: 1px solid {tokens.primary};
    }}
    QPushButton[role="primary"]:hover {{
        background: {tokens.primary_hover};
    }}
    QPushButton[role="secondary"] {{
        color: {tokens.text_primary};
        background: {tokens.surface};
        border: 1px solid {tokens.border};
    }}
    QPushButton:disabled {{
        color: #9CA3AF;
        background: #F3F4F6;
        border-color: #E5E7EB;
    }}
    QLineEdit {{
        min-height: 38px;
        padding: 0 12px;
        background: {tokens.surface};
        border: 1px solid {tokens.border};
        border-radius: {tokens.radius_control}px;
        selection-background-color: {tokens.primary};
    }}
    QLineEdit:focus {{
        border: 1px solid {tokens.primary};
    }}
    """


def apply_light_theme(app: QApplication) -> None:
    app.setStyleSheet(build_light_stylesheet())
```

- [ ] **Step 4: 实现基础组件**

```python
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class Card(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("role", "card")


class SectionTitle(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        font = self.font()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)


class StatCard(Card):
    def __init__(self, title: str, subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.value_label = QLabel("0")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("role", "muted")
        value_font = self.value_label.font()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class StatusChip(QWidget):
    TONES = {"success", "warning", "danger", "neutral", "primary"}

    def __init__(self, text: str = "", tone: str = "neutral", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.dot = QLabel("●")
        self.text_label = QLabel(text)
        layout.addWidget(self.dot)
        layout.addWidget(self.text_label)
        layout.addStretch(1)
        self.set_status(text, tone)

    def set_status(self, text: str, tone: str) -> None:
        if tone not in self.TONES:
            raise ValueError(f"unsupported tone: {tone}")
        colors = {
            "success": "#16A34A",
            "warning": "#D97706",
            "danger": "#DC2626",
            "neutral": "#6B7280",
            "primary": "#2563EB",
        }
        self.dot.setStyleSheet(f"color: {colors[tone]};")
        self.text_label.setText(text)
```

- [ ] **Step 5: 增加组件 GREEN 测试并运行**

Append to `tests/test_desktop_theme.py`:

```python
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from desktop.ui.components import StatCard, StatusChip


def test_fluent_components_update_display_state():
    app = QApplication.instance() or QApplication([])
    stat = StatCard("今日扫描", "邮件")
    stat.set_value("12")
    assert stat.value_label.text() == "12"

    chip = StatusChip()
    chip.set_status("正在运行", "success")
    assert chip.text_label.text() == "正在运行"
```

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_desktop_theme.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add desktop/ui/theme.py desktop/ui/components.py tests/test_desktop_theme.py
git commit -m "feat: add Fluent desktop design system"
```

---

### Task 2: 重构 Dashboard 为 Fluent 驾驶舱

**Files:**
- Modify: `desktop/ui/dashboard_window.py`
- Modify: `tests/test_desktop_app_smoke.py`

**Interfaces:**
- Consumes: `Card`, `StatCard`, `StatusChip`, `SectionTitle`, `DashboardSnapshot`, `AppStatus`
- Preserves constructor callbacks: `on_pause`, `on_resume`, `on_run_now`, `on_settings`
- Preserves action attributes: `pause_button`, `run_now_button`, `settings_button`
- Produces display attributes: `status_label`, `status_chip`, `last_check_label`, `next_check_label`, `scanned_card`, `inquiries_card`, `drafts_card`, `history_label`, `style_label`, `wecom_label`, `recent_table`

- [ ] **Step 1: 写新版 Dashboard RED 测试**

Replace only the visual assertions in `tests/test_desktop_app_smoke.py` while preserving scheduler/gate tests:

```python
def test_dashboard_renders_fluent_operational_summary():
    from desktop.models import ProcessRecord

    app = QApplication.instance() or QApplication([])
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

    assert window.status_chip.text_label.text() == "正在运行"
    assert window.scanned_card.value_label.text() == "12"
    assert window.inquiries_card.value_label.text() == "2"
    assert window.drafts_card.value_label.text() == "2"
    assert window.last_check_label.text() == "上次：刚刚"
    assert window.next_check_label.text() == "下次：2 分 48 秒后"
    assert window.history_label.text() == "已完成"
    assert window.style_label.text() == "已学习"
    assert window.wecom_label.text() == "已连接"
    assert window.recent_table.rowCount() == 1
```

Keep the existing tests for:

```text
pause/resume callbacks
run-now callback
settings callback
no send button
WAITING_INITIALIZATION action disabled
SERVICE_ERROR action disabled
NEEDS_ATTENTION action enabled
DesktopApplication production gate
```

- [ ] **Step 2: 运行 RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_desktop_app_smoke.py -v
```

Expected: FAIL because `status_chip`, `scanned_card`, `inquiries_card`, `drafts_card` do not yet exist.

- [ ] **Step 3: 重构 Dashboard 布局**

`DashboardWindow.__init__()` 使用以下布局顺序：

```text
Header
  外贸数字员工
  AI Foreign Trade Assistant
  status_chip
  settings_button

今日概览
  scanned_card | inquiries_card | drafts_card

服务状态 Card
  邮箱 / AI / 企业微信

自动检查 Card
  last_check_label | next_check_label

学习状态 Card
  历史邮件 / 回复风格

最近处理 Card
  recent_table <= 10

Bottom Actions
  pause_button | run_now_button(primary)
```

Implementation requirements:

```python
central_widget.setObjectName("AppRoot")
self.settings_button.setProperty("role", "secondary")
self.pause_button.setProperty("role", "secondary")
self.run_now_button.setProperty("role", "primary")

self.scanned_card = StatCard("今日扫描", "邮件")
self.inquiries_card = StatCard("新询盘", "待查看")
self.drafts_card = StatCard("已生成草稿", "163 草稿箱")
self.status_chip = StatusChip("等待初始化", "neutral")
```

Keep `recent_table` for V1 testability, but style it as a compact list:

```python
self.recent_table.verticalHeader().setVisible(False)
self.recent_table.setShowGrid(False)
self.recent_table.setAlternatingRowColors(False)
self.recent_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
self.recent_table.horizontalHeader().setStretchLastSection(True)
self.recent_table.setMaximumHeight(250)
```

- [ ] **Step 4: 更新 `render()` 的视觉文案与状态 tone**

Use:

```python
status_visual = {
    AppStatus.WAITING_INITIALIZATION: ("等待初始化", "neutral"),
    AppStatus.RUNNING: ("正在运行", "success"),
    AppStatus.PAUSED: ("已暂停", "neutral"),
    AppStatus.NEEDS_ATTENTION: ("需要处理", "warning"),
    AppStatus.SERVICE_ERROR: ("服务异常", "danger"),
}
text, tone = status_visual[snapshot.status]
self.status_label.setText(text)
self.status_chip.set_status(text, tone)

self.scanned_card.set_value(str(snapshot.today_scanned))
self.inquiries_card.set_value(str(snapshot.today_new_inquiries))
self.drafts_card.set_value(str(snapshot.today_drafts))
self.last_check_label.setText(f"上次：{snapshot.last_check_at or '--'}")
self.next_check_label.setText(f"下次：{snapshot.next_check_at or '--'}")
self.history_label.setText("已完成" if snapshot.history_ready else "未完成")
self.style_label.setText("已学习" if snapshot.style_ready else "未学习")
self.wecom_label.setText("已连接" if snapshot.wecom_connected else "未连接")
```

Preserve the existing enable/disable rules and pause/resume behavior exactly.

- [ ] **Step 5: 运行 Dashboard GREEN + focused regression**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py \
  tests/test_desktop_theme.py \
  tests/test_desktop_health.py \
  -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add desktop/ui/dashboard_window.py tests/test_desktop_app_smoke.py
git commit -m "feat: restyle desktop dashboard with Fluent UI"
```

---

### Task 3: 实现 Fluent 首次配置向导，历史学习强制完成

**Files:**
- Create: `desktop/ui/onboarding_window.py`
- Modify: `tests/test_desktop_app_smoke.py`

**Interfaces:**
- Produces: `OnboardingWindow`
- Constructor callbacks:
  - `on_test_mail(email: str, auth_code: str) -> bool`
  - `on_save_identity(name: str, title: str, company: str) -> None`
  - `is_ai_configured() -> bool`
  - `on_test_wecom(webhook: str) -> bool`
  - `on_learn_history() -> object` where `.failed` is an `int`
  - `on_complete() -> None`
- Produces public test attributes: `stack`, `email_edit`, `auth_code_edit`, `test_mail_button`, `email_next_button`, `email_status_label`, `name_edit`, `title_edit`, `company_edit`, `identity_next_button`, `ai_status_label`, `ai_next_button`, `wecom_edit`, `test_wecom_button`, `wecom_status_label`, `wecom_next_button`, `history_description`, `learn_history_button`, `history_status_label`, `finish_button`

- [ ] **Step 1: 写 5 步向导 RED 测试**

Append:

```python
def test_onboarding_window_requires_history_before_completion():
    from desktop.ui.onboarding_window import OnboardingWindow

    app = QApplication.instance() or QApplication([])
    calls = []

    class Summary:
        failed = 0

    window = OnboardingWindow(
        on_test_mail=lambda email, auth: True,
        on_save_identity=lambda name, title, company: calls.append("identity"),
        is_ai_configured=lambda: True,
        on_test_wecom=lambda webhook: True,
        on_learn_history=lambda: Summary(),
        on_complete=lambda: calls.append("complete"),
    )

    assert window.stack.currentIndex() == 0
    assert window.finish_button.isEnabled() is False

    window.email_edit.setText("sales@163.com")
    window.auth_code_edit.setText("secret")
    window.test_mail_button.click()
    assert window.email_status_label.text() == "邮箱连接正常"
    assert window.email_next_button.isEnabled() is True
    window.email_next_button.click()

    window.name_edit.setText("Alice")
    window.identity_next_button.click()
    assert window.stack.currentIndex() == 2
    assert window.ai_status_label.text() == "AI 服务已配置"
    window.ai_next_button.click()

    window.wecom_edit.setText("https://example.invalid/hook")
    window.test_wecom_button.click()
    assert window.wecom_status_label.text() == "企业微信已连接"
    window.wecom_next_button.click()

    assert window.stack.currentIndex() == 4
    assert "历史邮件只用于学习" in window.history_description.text()
    assert "1000" not in window.history_description.text()
    assert "6 months" not in window.history_description.text()
    assert window.finish_button.isEnabled() is False

    window.learn_history_button.click()
    assert window.history_status_label.text() == "历史学习已完成"
    assert window.finish_button.isEnabled() is True
    window.finish_button.click()
    assert calls[-1] == "complete"
```

Add a failure test:

```python
def test_onboarding_history_failure_keeps_finish_locked():
    from desktop.ui.onboarding_window import OnboardingWindow

    class Summary:
        failed = 1

    app = QApplication.instance() or QApplication([])
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
    assert window.finish_button.isEnabled() is False
    assert window.learn_history_button.isEnabled() is True
```

- [ ] **Step 2: 运行 RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py::test_onboarding_window_requires_history_before_completion \
  tests/test_desktop_app_smoke.py::test_onboarding_history_failure_keeps_finish_locked \
  -v
```

Expected: FAIL because `desktop.ui.onboarding_window` does not exist.

- [ ] **Step 3: 实现 Fluent 向导壳**

Use one `QStackedWidget` and a shared header:

```text
外贸数字员工
首次配置
1 邮箱  2 身份  3 AI  4 企业微信  5 学习
```

Every page uses a white `Card`, `SectionTitle`, muted description labels, and primary/secondary button roles. Inputs keep existing QLineEdit widgets so tests and cross-platform behavior remain simple.

Required page copy:

```text
邮箱：绑定你的 163 邮箱
说明：只读取邮件并生成草稿，不会自动发送。

身份：告诉数字员工你是谁
职位、公司允许留空。

AI：AI 服务已配置
普通用户不显示 provider/model/base URL/API Key。

企业微信：连接企业微信通知
Webhook 字段使用 Password echo mode。

学习：让数字员工学习你的历史邮件
历史邮件只用于学习，不会回复旧邮件，也不会发送任何邮件。
```

- [ ] **Step 4: 实现强制历史学习状态机**

Required logic:

```python
def _learn_history(self, checked: bool = False) -> None:
    del checked
    self.learn_history_button.setEnabled(False)
    self.finish_button.setEnabled(False)
    self.history_status_label.setText("正在学习历史邮件…")
    try:
        summary = self._on_learn_history()
    except Exception:
        self.history_status_label.setText("历史学习失败，请重试")
        self.learn_history_button.setEnabled(True)
        return

    if int(getattr(summary, "failed", 0)) > 0:
        self.history_status_label.setText("历史学习未完成，请重试")
        self.learn_history_button.setEnabled(True)
        return

    self.history_status_label.setText("历史学习已完成")
    self.finish_button.setEnabled(True)
```

There is no “跳过”, “稍后学习”, or alternative route to `on_complete()`.

- [ ] **Step 5: 运行 GREEN + onboarding service regression**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py \
  tests/test_desktop_onboarding.py \
  tests/test_history_reply_baseline.py \
  -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add desktop/ui/onboarding_window.py tests/test_desktop_app_smoke.py
git commit -m "feat: add Fluent first-run onboarding"
```

---

### Task 4: 实现普通设置页与管理员入口

**Files:**
- Create: `desktop/ui/settings_dialog.py`
- Modify: `tests/test_desktop_app_smoke.py`

**Interfaces:**
- Produces: `SettingsDialog`
- Constructor data: `settings: DesktopSettings`
- Constructor callbacks:
  - `on_save_identity(name: str, title: str, company: str) -> None`
  - `on_toggle_autostart(enabled: bool) -> None`
  - `on_toggle_desktop_notifications(enabled: bool) -> None`
  - `on_test_mail() -> bool`
  - `on_test_wecom() -> bool`
  - `on_relearn_history() -> None`
  - `on_open_admin() -> None`
- Public attributes for tests: `name_edit`, `title_edit`, `company_edit`, `autostart_checkbox`, `notifications_checkbox`, `test_mail_button`, `test_wecom_button`, `relearn_button`, `admin_button`

- [ ] **Step 1: 写普通设置安全边界 RED 测试**

```python
def test_settings_dialog_exposes_only_normal_user_settings():
    from PySide6.QtWidgets import QLineEdit
    from desktop.models import DesktopSettings
    from desktop.ui.settings_dialog import SettingsDialog

    app = QApplication.instance() or QApplication([])
    calls = []
    dialog = SettingsDialog(
        settings=DesktopSettings(
            sender_name="Alice",
            sender_title="Sales Manager",
            sender_company="Example Co.",
            autostart_enabled=True,
            desktop_notifications_enabled=True,
        ),
        on_save_identity=lambda n, t, c: calls.append((n, t, c)),
        on_toggle_autostart=lambda enabled: calls.append(("autostart", enabled)),
        on_toggle_desktop_notifications=lambda enabled: calls.append(("notify", enabled)),
        on_test_mail=lambda: True,
        on_test_wecom=lambda: True,
        on_relearn_history=lambda: calls.append(("relearn",)),
        on_open_admin=lambda: calls.append(("admin",)),
    )

    assert dialog.name_edit.text() == "Alice"
    assert dialog.admin_button.text() == "高级设置"

    visible_text = " ".join(
        widget.text()
        for widget in dialog.findChildren(QLineEdit)
    )
    assert "api_key" not in visible_text.lower()
    assert "base_url" not in visible_text.lower()
    assert "imap.163.com" not in visible_text.lower()
```

Also assert the dialog has no line edit object names containing:

```text
api_key
base_url
imap_host
imap_port
history_months
history_limit
log_level
```

- [ ] **Step 2: 运行 RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py::test_settings_dialog_exposes_only_normal_user_settings \
  -v
```

Expected: FAIL because `desktop.ui.settings_dialog` does not exist.

- [ ] **Step 3: 实现普通设置 Dialog**

Sections:

```text
账户
  163 邮箱：只显示当前邮箱与“已连接/需检查”状态

个人信息
  姓名 / 职位 / 公司

通知
  企业微信连接状态
  桌面通知 checkbox

工作方式
  开机自动启动 checkbox

学习
  历史邮件 / 回复风格 / 客户记忆摘要
  重新学习历史邮件

高级设置
  [高级设置]  -> on_open_admin()
```

Implementation requirements:

```python
self.admin_button.setProperty("role", "secondary")
self.save_button.setProperty("role", "primary")
```

No secret field exists in the ordinary dialog.

- [ ] **Step 4: GREEN + safety regression**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py \
  tests/test_desktop_settings_store.py \
  tests/test_desktop_credentials.py \
  -v
```

Expected: PASS and existing secret-storage tests remain unchanged.

- [ ] **Step 5: Commit**

```bash
git add desktop/ui/settings_dialog.py tests/test_desktop_app_smoke.py
git commit -m "feat: add Fluent normal settings dialog"
```

---

### Task 5: 顶层应用在首次向导与 Dashboard 之间切换

**Files:**
- Modify: `desktop/app.py`
- Modify: `tests/test_desktop_app_smoke.py`

**Interfaces:**
- Preserves `DesktopApplication.pause()`, `resume()`, `run_now()`
- Changes constructor to accept:
  - `dashboard_window`
  - `onboarding_window`
  - `scheduler`
  - `ready_check`
- `show() -> None` shows Dashboard and starts scheduler only when `ready_check()` is True; otherwise shows Onboarding and does not start scheduler.
- `on_onboarding_complete() -> None` re-checks readiness, closes/hides onboarding, shows Dashboard, and starts scheduler exactly once.

- [ ] **Step 1: 写页面切换 RED 测试**

```python
def test_desktop_application_shows_onboarding_before_ready():
    from desktop.app import DesktopApplication

    class FakeWindow:
        def __init__(self):
            self.show_calls = 0
            self.hide_calls = 0
        def show(self):
            self.show_calls += 1
        def hide(self):
            self.hide_calls += 1

    class FakeScheduler:
        def __init__(self):
            self.start_calls = 0
        def start(self):
            self.start_calls += 1
            return True
        def pause(self): pass
        def resume(self): pass
        def run_now(self): return None

    dashboard = FakeWindow()
    onboarding = FakeWindow()
    scheduler = FakeScheduler()
    ready = {"value": False}

    desktop = DesktopApplication(
        dashboard_window=dashboard,
        onboarding_window=onboarding,
        scheduler=scheduler,
        ready_check=lambda: ready["value"],
    )

    desktop.show()
    assert onboarding.show_calls == 1
    assert dashboard.show_calls == 0
    assert scheduler.start_calls == 0

    ready["value"] = True
    desktop.on_onboarding_complete()
    assert onboarding.hide_calls == 1
    assert dashboard.show_calls == 1
    assert scheduler.start_calls == 1
```

Keep a second test that when ready at startup, Dashboard shows immediately and scheduler starts once.

- [ ] **Step 2: 运行 RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py::test_desktop_application_shows_onboarding_before_ready \
  -v
```

Expected: FAIL because the current `DesktopApplication` accepts only `window=`.

- [ ] **Step 3: 实现最小页面控制器**

```python
class DesktopApplication:
    def __init__(
        self,
        *,
        dashboard_window,
        onboarding_window,
        scheduler,
        ready_check,
    ) -> None:
        self.dashboard_window = dashboard_window
        self.onboarding_window = onboarding_window
        self.scheduler = scheduler
        self.ready_check = ready_check
        self._scheduler_started = False

    def _start_scheduler_once(self) -> None:
        if self._scheduler_started:
            return
        if self.scheduler.start():
            self._scheduler_started = True

    def show(self) -> None:
        if self.ready_check():
            self.dashboard_window.show()
            self._start_scheduler_once()
            return
        self.onboarding_window.show()

    def on_onboarding_complete(self) -> None:
        if not self.ready_check():
            return
        self.onboarding_window.hide()
        self.dashboard_window.show()
        self._start_scheduler_once()

    def pause(self) -> None:
        self.scheduler.pause()

    def resume(self) -> None:
        self.scheduler.resume()

    def run_now(self):
        return self.scheduler.run_now()
```

- [ ] **Step 4: 更新旧 App smoke tests 到新构造签名**

Replace old `window=FakeWindow()` calls with:

```python
dashboard_window=FakeWindow(),
onboarding_window=FakeWindow(),
```

Do not weaken assertions about production gate or scheduler call counts.

- [ ] **Step 5: GREEN + focused regression**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py \
  tests/test_desktop_scheduler.py \
  tests/test_desktop_onboarding.py \
  -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add desktop/app.py tests/test_desktop_app_smoke.py
git commit -m "feat: route first run through Fluent onboarding"
```

---

### Task 6: 应用浅色主题、完成全回归与真机视觉预览

**Files:**
- Modify: `desktop/app.py`
- Modify: `tests/test_desktop_app_smoke.py`

**Interfaces:**
- Consumes: `apply_light_theme(app)`
- `main() -> int` applies the theme before showing any window.

- [ ] **Step 1: 写主题入口 RED 测试**

Add an injectable helper:

```python
def test_apply_theme_hook_runs_before_desktop_show(monkeypatch):
    from desktop import app as app_module

    calls = []
    monkeypatch.setattr(
        app_module,
        "apply_light_theme",
        lambda qapp: calls.append("theme"),
    )

    class FakeDesktop:
        def show(self):
            calls.append("show")

    app_module.prepare_desktop_ui(
        qapp=object(),
        desktop=FakeDesktop(),
    )

    assert calls == ["theme", "show"]
```

- [ ] **Step 2: 运行 RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_app_smoke.py::test_apply_theme_hook_runs_before_desktop_show \
  -v
```

Expected: FAIL because `prepare_desktop_ui` does not exist.

- [ ] **Step 3: 实现主题入口 helper**

```python
from desktop.ui.theme import apply_light_theme


def prepare_desktop_ui(*, qapp, desktop) -> None:
    apply_light_theme(qapp)
    desktop.show()
```

`main()` uses this helper before `app.exec()`.

- [ ] **Step 4: focused regression**

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_desktop_theme.py \
  tests/test_desktop_app_smoke.py \
  tests/test_desktop_health.py \
  tests/test_desktop_onboarding.py \
  tests/test_desktop_scheduler.py \
  -v
```

Expected: PASS.

- [ ] **Step 5: full local regression**

Run real-network tests separately to avoid treating transient IMAP EOF as a UI regression:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q \
  -k "not test_can_fetch_latest_raw_email_without_modifying_mailbox and not test_can_login_to_real_imap_mailbox"
```

Expected: all selected local tests PASS, no failures/errors.

Then:

```bash
python -m pytest \
  tests/test_fetch_latest_mail.py::test_can_fetch_latest_raw_email_without_modifying_mailbox \
  tests/test_imap_connection.py::test_can_login_to_real_imap_mailbox \
  -q
```

Expected: `2 passed`. If this fails with a socket EOF, retry once before classifying it as a code regression.

- [ ] **Step 6: 手工视觉预览**

Run the actual QWidget Dashboard with the real light theme and demo-only snapshot. The preview must not call IMAP, AI, history learning, or WeCom.

Acceptance checklist:

```text
[ ] 背景为冷灰白，不再是默认 Qt 灰
[ ] 三个统计卡片层级清楚
[ ] 主按钮只有“立即检查邮件”为蓝色强调
[ ] 设置入口位于 Header，不与主操作抢层级
[ ] 正常状态使用绿色圆点，不大量使用 emoji
[ ] 最近处理区域紧凑，没有巨大的空白表格
[ ] macOS 字体与 Windows 系统字体自然回退
[ ] 无“发送邮件”按钮
```

- [ ] **Step 7: final full regression**

Run:

```bash
python -m pytest -q
```

If the two live-IMAP tests are unstable, record their separate passing run together with the local suite result; do not delete or skip them permanently.

- [ ] **Step 8: Commit**

```bash
git add desktop/app.py desktop/ui tests/test_desktop_theme.py tests/test_desktop_app_smoke.py
git commit -m "feat: complete Fluent desktop UI foundation"
```

---

## Plan Self-Review

### Spec coverage

- Fluent light visual tokens: Task 1.
- QWidget retained, no QML migration: global constraint + Tasks 1-6.
- Dashboard cards/status/list/actions: Task 2.
- No send button / no email body / no secrets: Tasks 2 and 4 regression requirements.
- Mandatory 5-step onboarding with history-learning gate: Task 3.
- Ordinary settings only: Task 4.
- Admin entry exists but secure PIN implementation remains the already-scoped Desktop V1 Task 10: global constraint + Task 4.
- First-run onboarding vs ready Dashboard routing: Task 5.
- Theme applied at application entry: Task 6.
- Mac/Windows shared UI code: global constraint.
- Dark mode excluded from V1: global constraint.

### Placeholder scan

The plan contains no `TODO`, `TBD`, “implement later”, or unspecified code steps. The administrator PIN cryptographic implementation is explicitly outside this UI sub-project and remains owned by the existing Desktop V1 PIN task rather than being an unresolved placeholder.

### Type consistency

- `DashboardSnapshot` / `AppStatus` remain unchanged.
- Existing Dashboard action callbacks remain `on_pause`, `on_resume`, `on_run_now`, `on_settings`.
- New `OnboardingWindow` callbacks map directly to existing OnboardingService operations at integration time.
- `DesktopApplication` uses one scheduler and one `ready_check`; no second production pipeline is introduced.
