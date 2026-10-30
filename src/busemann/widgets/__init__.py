"""Reusable themed widgets."""
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel

from ..theme import qt as theme
from .collapsible import CollapsibleSection
from .kpi_card import KpiCard
from .labeled_slider import LabeledSlider
from .number_field import NumberField
from .segmented import SegmentedControl


def section_title(text):
    label = QLabel(theme.caps(text))
    label.setObjectName("sectionTitle")
    label.setFont(theme.label_font(QFont.Weight.DemiBold))
    return label


def field_label(text, tooltip=""):
    label = QLabel(theme.caps(text))
    label.setObjectName("fieldLabel")
    label.setFont(theme.label_font())
    label.setToolTip(tooltip)
    return label


def divider():
    line = QFrame()
    line.setObjectName("divider")
    line.setFrameShape(QFrame.Shape.NoFrame)
    return line


__all__ = [
    "CollapsibleSection", "KpiCard", "LabeledSlider", "NumberField", "SegmentedControl",
    "section_title", "field_label", "divider",
]
