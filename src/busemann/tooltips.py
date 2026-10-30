"""One-sentence tooltips (with units) for every label, KPI, table header and chart axis.

All texts live in resources/explain/tooltips.json; tip(key) raises KeyError for an unknown
key, so a missing tooltip is a bug, not a blank. Importing this module does not need Qt.
"""
import json
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def tooltips():
    text = resources.files("busemann").joinpath("resources", "explain", "tooltips.json")
    return json.loads(text.read_text(encoding="utf-8"))


def tip(key):
    """Tooltip text for `key`; KeyError if the key is not in tooltips.json."""
    return tooltips()[key]


def attach(widget, key_or_text, is_key=True):
    """Set the tooltip on `widget` and on every descendant label or line edit that has none
    (value and unit labels of a row share the row's tooltip). GUI code only."""
    from PySide6.QtWidgets import QLabel, QLineEdit

    text = tip(key_or_text) if is_key else key_or_text
    widget.setToolTip(text)
    for cls in (QLabel, QLineEdit):
        for child in widget.findChildren(cls):
            if not child.toolTip():
                child.setToolTip(text)
    return widget
