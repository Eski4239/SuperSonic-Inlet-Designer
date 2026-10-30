"""Placeholder for the inlet canvas (replaced by InletScene in milestone M3)."""
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView

from .. import theme
from ..theme import tokens


class CanvasPlaceholder(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        scene = QGraphicsScene(self)
        scene.setBackgroundBrush(QBrush(QColor(tokens.COLORS["surface"])))
        text = scene.addText("Inlet canvas — milestone M3", theme.ui_font(tokens.SIZE_BASE))
        text.setDefaultTextColor(QColor(tokens.COLORS["text_muted"]))
        self.setScene(scene)
