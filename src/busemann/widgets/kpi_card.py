"""KPI card: uppercase title, large mono value, muted mono unit, optional sub-line."""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from .. import theme
from ..theme import tokens

EMPTY = "—"


class KpiCard(QFrame):
    def __init__(self, title, tooltip="", parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setToolTip(tooltip)

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

        value_row = QHBoxLayout()
        value_row.setSpacing(tokens.space(1) // 2)
        value_row.addWidget(self.value_label)
        value_row.addWidget(self.unit_label)
        value_row.addStretch(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(tokens.space(2), tokens.space(1) + 4, tokens.space(2),
                                  tokens.space(1) + 4)
        layout.setSpacing(2)
        layout.addWidget(self.title)
        layout.addLayout(value_row)
        layout.addWidget(self.sub_label)

    def set_value(self, text, unit="", sub=None):
        self.value_label.setText(text)
        self.unit_label.setText(unit)
        self.sub_label.setText(sub or "")
        self.sub_label.setVisible(bool(sub))

    def clear(self):
        self.set_value(EMPTY)

    def text(self):
        return self.value_label.text()
