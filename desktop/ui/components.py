from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class Card(QFrame):
    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setProperty(
            "role",
            "card",
        )


class SectionTitle(QLabel):
    def __init__(
        self,
        text: str,
        parent=None,
    ) -> None:
        super().__init__(
            text,
            parent,
        )

        self.setProperty(
            "role",
            "section-title",
        )

        font = self.font()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)


class StatCard(Card):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(6)

        self.title_label = QLabel(
            title
        )

        self.title_label.setProperty(
            "role",
            "muted",
        )

        self.value_label = QLabel(
            "0"
        )

        value_font = (
            self.value_label.font()
        )

        value_font.setPointSize(
            24
        )

        value_font.setBold(
            True
        )

        self.value_label.setFont(
            value_font
        )

        self.subtitle_label = QLabel(
            subtitle
        )

        self.subtitle_label.setProperty(
            "role",
            "muted",
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            self.subtitle_label
        )

    def set_value(
        self,
        value: str,
    ) -> None:
        self.value_label.setText(
            value
        )


class StatusChip(QWidget):
    TONES = {
        "success",
        "warning",
        "danger",
        "neutral",
        "primary",
    }

    COLORS = {
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
        "neutral": "#6B7280",
        "primary": "#2563EB",
    }

    def __init__(
        self,
        text: str = "",
        tone: str = "neutral",
        parent=None,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            6
        )

        self.dot = QLabel(
            "●"
        )

        self.text_label = QLabel(
            text
        )

        layout.addWidget(
            self.dot
        )

        layout.addWidget(
            self.text_label
        )

        layout.addStretch(
            1
        )

        self.set_status(
            text,
            tone,
        )

    def set_status(
        self,
        text: str,
        tone: str,
    ) -> None:
        if tone not in self.TONES:
            raise ValueError(
                f"unsupported tone: {tone}"
            )

        self.dot.setStyleSheet(
            f"color: {self.COLORS[tone]};"
        )

        self.text_label.setText(
            text
        )
