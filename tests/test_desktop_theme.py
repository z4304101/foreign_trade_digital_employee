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

    assert "#AppRoot" in qss
    assert 'QPushButton[role="primary"]' in qss
    assert 'QPushButton[role="secondary"]' in qss
    assert 'QFrame[role="card"]' in qss
    assert "QLineEdit" in qss


import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import QApplication

from desktop.ui.components import (
    StatCard,
    StatusChip,
)


def test_fluent_components_update_display_state():
    app = (
        QApplication.instance()
        or QApplication([])
    )

    stat = StatCard(
        "今日扫描",
        "邮件",
    )

    stat.set_value(
        "12"
    )

    assert (
        stat.value_label.text()
        == "12"
    )

    chip = StatusChip()

    chip.set_status(
        "正在运行",
        "success",
    )

    assert (
        chip.text_label.text()
        == "正在运行"
    )
