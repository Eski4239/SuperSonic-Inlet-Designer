"""Read-only label | mono value | muted unit grid."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from inletdesign import units as _units

from ..theme import qt as theme
from ..theme import tokens
from ..tooltips import tip
from . import format as fmt


class Readout(QWidget):
    def __init__(self, rows, parent=None):
        """rows: list of (key, label, quantity or None, tooltip key). quantity selects units;
        the tooltip (tooltips.json) is shared by the row's label, value and unit."""
        super().__init__(parent)
        self._rows = {}
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(tokens.space(1))
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(1, 1)
        for r, (key, label, quantity, tip_key) in enumerate(rows):
            tooltip = tip(tip_key)
            name = QLabel(label)
            name.setObjectName("readoutLabel")
            name.setToolTip(tooltip)
            value = QLabel("—")
            value.setObjectName("readoutValue")
            value.setFont(theme.mono_font())
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value.setWordWrap(True)      # long angle lists (4 ramps) wrap instead of widening
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            unit = QLabel()
            unit.setObjectName("readoutUnit")
            unit.setFont(theme.mono_font(tokens.SIZE_LABEL))
            unit.setMinimumWidth(tokens.space(7))
            value.setToolTip(tooltip)
            unit.setToolTip(tooltip)
            grid.addWidget(name, r, 0)
            grid.addWidget(value, r, 1)
            grid.addWidget(unit, r, 2)
            self._rows[key] = (quantity, value, unit)

    def set_si(self, key, value_si, system, digits=4):
        """Show an SI value converted to the display unit of its quantity."""
        quantity, value, unit = self._rows[key]
        if value_si is None:
            value.setText("—")
        else:
            value.setText(fmt.sig(_units.to_display(value_si, quantity, system), digits))
        unit.setText(_units.unit_label(quantity, system))

    def set_text(self, key, text, unit_text=""):
        _, value, unit = self._rows[key]
        value.setText(text)
        unit.setText(unit_text)

    def text(self, key):
        return self._rows[key][1].text()

    def unit(self, key):
        return self._rows[key][2].text()
