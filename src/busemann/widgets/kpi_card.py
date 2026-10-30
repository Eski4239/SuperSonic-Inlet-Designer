"""KPI card: uppercase title, large mono value, muted mono unit, optional sub-line."""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ..theme import qt as theme
from ..tooltips import attach
from ..theme import tokens

EMPTY = "—"


class KpiCard(QFrame):
    def __init__(self, title, key, parent=None):
        """`key` names the card's tooltip in tooltips.json (shared by all its labels)."""
        super().__init__(parent)
        self.setObjectName("kpiCard")

        self.title = QLabel(theme.caps(title))
        self.title.setObjectName("kpiTitle")
        self.title.setFont(theme.label_font())
        self.value_label = QLabel(EMPTY)
        self.value_label.setObjectName("kpiValue")
        self.value_label.setFont(theme.mono_font(tokens.SIZE_KPI))
        self.unit_label = QLabel()
        self.unit_label.setObjectName("unit")
        self.unit_label.setFont(theme.mono_font(tokens.SIZE_LABEL))
        self.sub_label = QLabel()
        self.sub_label.setObjectName("kpiSub")
        self.sub_label.hide()
        self.delta_label = QLabel()
        self.delta_label.setObjectName("kpiDelta")
        self.delta_label.setFont(theme.mono_font(tokens.SIZE_LABEL))
        self.delta_label.hide()
        self.badge = QLabel()
        self.badge.setObjectName("kpiBadge")
        self.badge.setFont(theme.label_font())
        self.badge.hide()

        value_row = QHBoxLayout()
        value_row.setSpacing(tokens.space(1) // 2)
        value_row.addWidget(self.value_label)
        value_row.addWidget(self.unit_label)
        value_row.addStretch(1)
        value_row.addWidget(self.badge)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(tokens.space(2), tokens.space(1) + 4, tokens.space(2),
                                  tokens.space(1) + 4)
        layout.setSpacing(2)
        layout.addWidget(self.title)
        layout.addLayout(value_row)
        layout.addWidget(self.sub_label)
        layout.addWidget(self.delta_label)
        attach(self, key)

    def set_value(self, text, unit="", sub=None):
        self.value_label.setText(text)
        self.unit_label.setText(unit)
        self.sub_label.setText(sub or "")
        self.sub_label.setVisible(bool(sub))

    def set_delta(self, text=None):
        """Small muted "Δ vs design" line under the value; None hides it."""
        self.delta_label.setText(f"Δ vs design {text}" if text else "")
        self.delta_label.setVisible(bool(text))

    def set_badge(self, text=None):
        """Small accent tag next to the value (e.g. CONSTRAINED); None hides it."""
        self.badge.setText(theme.caps(text) if text else "")
        self.badge.setVisible(bool(text))

    def clear(self, sub=None):
        self.set_value(EMPTY, sub=sub)
        self.set_badge(None)
        self.set_delta(None)

    def text(self):
        return self.value_label.text()
