from dataclasses import dataclass

from desktop.health import AppStatus


@dataclass
class DesktopSettings:
    email_user: str = ""

    sender_name: str = ""
    sender_title: str = ""
    sender_company: str = ""

    imap_host: str = "imap.163.com"
    imap_port: int = 993

    llm_provider: str = "siliconflow"
    llm_model: str = ""
    llm_base_url: str = ""

    poll_interval_seconds: int = 180

    autostart_enabled: bool = True
    desktop_notifications_enabled: bool = True
    wecom_enabled: bool = True

    history_months: int = 6
    history_limit: int = 1000

    log_level: str = "INFO"

    onboarding_completed: bool = False
    baseline_completed: bool = False


@dataclass(frozen=True)
class ProcessRecord:
    """
    Lightweight summary shown in the desktop dashboard.

    Intentionally does NOT store the full customer
    email body.
    """

    sender: str
    subject: str
    processed_at: str

    analysis_completed: bool = False
    draft_saved: bool = False
    wecom_notified: bool = False


@dataclass(frozen=True)
class DashboardSnapshot:
    """
    Current dashboard state.

    This contains only operational/status information.
    It does not contain customer email bodies or secrets.
    """

    status: AppStatus

    last_check_at: str = ""
    next_check_at: str = ""

    today_scanned: int = 0
    today_new_inquiries: int = 0
    today_drafts: int = 0

    history_ready: bool = False
    style_ready: bool = False
    wecom_connected: bool = False

    recent_records: tuple[ProcessRecord, ...] = ()
