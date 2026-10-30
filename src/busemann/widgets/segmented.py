"""Segmented control: a row of exclusive, joined toggle buttons."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QSizePolicy, QWidget


class SegmentedControl(QWidget):
    """changed(key) fires when the user picks a different segment."""

    changed = Signal(str)

    def __init__(self, options, current=None, parent=None):
        """options: list of (key, label)."""
        super().__init__(parent)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for i, (key, label) in enumerate(options):
            button = QPushButton(label)
            button.setObjectName("segment")
            button.setCheckable(True)
            button.setProperty("first", i == 0)
            button.setProperty("last", i == len(options) - 1)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._group.addButton(button, i)
            self._buttons[key] = button
            layout.addWidget(button)
            button.clicked.connect(lambda _=False, k=key: self.changed.emit(k))
        self.set_current(current if current is not None else options[0][0])

    def current(self):
        for key, button in self._buttons.items():
            if button.isChecked():
                return key
        return None

    def set_current(self, key):
        """Programmatic selection; does not emit."""
        self._buttons[key].setChecked(True)

    def button(self, key):
        return self._buttons[key]
