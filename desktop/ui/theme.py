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

    QLabel[role="section-title"] {{
        color: {tokens.text_primary};
        font-size: 15px;
        font-weight: 600;
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
        border-color: {tokens.primary_hover};
    }}

    QPushButton[role="secondary"] {{
        color: {tokens.text_primary};
        background: {tokens.surface};
        border: 1px solid {tokens.border};
    }}

    QPushButton[role="secondary"]:hover {{
        background: {tokens.surface_muted};
    }}

    QPushButton:disabled {{
        color: #9CA3AF;
        background: #F3F4F6;
        border-color: #E5E7EB;
    }}

    QLineEdit {{
        min-height: 38px;
        padding: 0 12px;
        color: {tokens.text_primary};
        background: {tokens.surface};
        border: 1px solid {tokens.border};
        border-radius: {tokens.radius_control}px;
        selection-background-color: {tokens.primary};
    }}

    QLineEdit:focus {{
        border: 1px solid {tokens.primary};
    }}

    QTableWidget {{
        background: {tokens.surface};
        border: none;
        gridline-color: {tokens.border};
        selection-background-color: #EFF6FF;
    }}

    QHeaderView::section {{
        color: {tokens.text_secondary};
        background: {tokens.surface_muted};
        border: none;
        border-bottom: 1px solid {tokens.border};
        padding: 8px;
        font-weight: 600;
    }}
    """


def apply_light_theme(
    app: QApplication,
) -> None:
    app.setStyleSheet(
        build_light_stylesheet()
    )
