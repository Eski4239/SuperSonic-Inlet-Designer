"""Compact per-ramp table: Ramp | θ | β | M after (mono, right-aligned numbers)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from ..theme import qt as theme
from ..theme import tokens

HEADERS = (("Ramp", ""), ("θ", "deg"), ("β", "deg"), ("M after", ""))


class RampTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rampTable")
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(tokens.space(2))
        self._grid.setVerticalSpacing(3)
        for c, (name, unit) in enumerate(HEADERS):
            text = f"{name} {unit}".strip()
            head = QLabel(text)
            head.setObjectName("readoutLabel")
            head.setAlignment(_align(c))
            self._grid.addWidget(head, 0, c)
            self._grid.setColumnStretch(c, 0 if c == 0 else 1)
        self._cells = []
        self.empty = QLabel("No ramps (pitot inlet)")
        self.empty.setObjectName("selectionHint")
        self._grid.addWidget(self.empty, 1, 0, 1, len(HEADERS))
        self.rows = []

    def set_rows(self, rows):
        """rows: [(theta_deg, beta_deg, M_after), ...]; [] shows the no-ramp note."""
        for w in self._cells:
            w.deleteLater()
        self._cells = []
        self.rows = list(rows)
        self.empty.setText("No ramps (pitot inlet)")
        self.empty.setVisible(not rows)
        for r, (theta, beta, mach) in enumerate(rows, start=1):
            for c, text in enumerate((str(r), f"{theta:.2f}", f"{beta:.2f}", f"{mach:.3f}")):
                cell = QLabel(text)
                cell.setObjectName("readoutValue")
                cell.setFont(theme.mono_font())
                cell.setAlignment(_align(c))
                self._grid.addWidget(cell, r, c)
                self._cells.append(cell)

    def clear(self):
        self.set_rows([])
        self.empty.setText("—")
        self.empty.show()

    def text(self, row, col):
        return self._cells[row * len(HEADERS) + col].text()


def _align(col):
    h = Qt.AlignmentFlag.AlignLeft if col == 0 else Qt.AlignmentFlag.AlignRight
    return h | Qt.AlignmentFlag.AlignVCenter
