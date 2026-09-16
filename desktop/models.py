from dataclasses import dataclass


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
