"""Numeric input with a muted mono unit suffix and inline validation (no dialogs, no clamping)."""
import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from .. import theme


class NumberField(QWidget):
    """Emits value_changed(float) only for valid input; invalid input shows a red underline + message.

    Bounds are checked, never applied: an out-of-range entry is reported, not clamped.
    """

    value_changed = Signal(float)

    def __init__(self, value=0.0, decimals=2, minimum=None, maximum=None,
                 min_exclusive=False, unit="", parent=None):
        super().__init__(parent)
        self._decimals = decimals
        self._min = minimum
        self._max = maximum
        self._min_exclusive = min_exclusive
        self._value = float(value)
        self._external_error = None

        self.edit = QLineEdit()
        self.edit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.edit.setFont(theme.mono_font())
        self.unit_label = QLabel(unit)
        self.unit_label.setObjectName("unit")
        self.unit_label.setFont(theme.mono_font(11))
        self.unit_label.setMinimumWidth(theme.tokens.space(4))
        self.error_label = QLabel()
        self.error_label.setObjectName("fieldError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(theme.tokens.space(1) // 2)
        row.addWidget(self.edit, 1)
        row.addWidget(self.unit_label)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addLayout(row)
        layout.addWidget(self.error_label)

        self.edit.editingFinished.connect(self._commit)
        self.edit.returnPressed.connect(self._commit)
        self._show_value()

    # --- public -------------------------------------------------------
    def value(self):
        return self._value

    def set_value(self, value, emit=False):
        self._value = float(value)
        self._show_value()
        self._set_error(self._external_error)  # keep errors reported by the core
        if emit:
            self.value_changed.emit(self._value)

    def set_unit(self, unit):
        self.unit_label.setText(unit)

    def set_range(self, minimum=None, maximum=None):
        self._min, self._max = minimum, maximum

    def set_decimals(self, decimals):
        self._decimals = decimals
        self._show_value()

    def set_external_error(self, message):
        """Error from elsewhere (e.g. the core rejected the value); None clears it."""
        self._external_error = message
        self._set_error(message)

    def error(self):
        return self.error_label.text() if self.error_label.isVisible() else None

    # --- internals ----------------------------------------------------
    def _show_value(self):
        self.edit.setText(f"{self._value:.{self._decimals}f}")

    def _set_error(self, message):
        self.edit.setProperty("invalid", bool(message))
        self.edit.style().unpolish(self.edit)
        self.edit.style().polish(self.edit)
        self.error_label.setText(message or "")
        self.error_label.setVisible(bool(message))

    def _validate(self, text):
        try:
            value = float(text.replace(",", "."))
        except ValueError:
            return None, "Enter a number"
        if not math.isfinite(value):
            return None, "Enter a finite number"
        low_bad = self._min is not None and (
            value <= self._min if self._min_exclusive else value < self._min
        )
        if low_bad or (self._max is not None and value > self._max):
            return None, self._range_message()
        return value, None

    def _range_message(self):
        unit = f" {self.unit_label.text()}" if self.unit_label.text() else ""
        fmt = lambda v: f"{v:.{self._decimals}f}".rstrip("0").rstrip(".")  # noqa: E731
        if self._min is not None and self._max is not None:
            op = ">" if self._min_exclusive else "≥"
            return f"Must be {op} {fmt(self._min)} and ≤ {fmt(self._max)}{unit}"
        if self._min is not None:
            return f"Must be {'>' if self._min_exclusive else '≥'} {fmt(self._min)}{unit}"
        return f"Must be ≤ {fmt(self._max)}{unit}"

    def _commit(self):
        value, message = self._validate(self.edit.text())
        if message:
            self._set_error(message)
            return
        self._set_error(self._external_error)
        changed = value != self._value
        self._value = value
        self._show_value()
        if changed:
            self.value_changed.emit(value)
