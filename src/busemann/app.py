"""QApplication setup and the main window (spec 5 layout: left 300 | canvas | right 320)."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QProgressBar, QScrollArea, QTabWidget,
    QToolBar, QVBoxLayout, QWidget,
)

from . import __version__, theme
from .canvas import CanvasPlaceholder
from .state import AppState
from .theme import tokens
from .views import DesignPanel, FlightPanel, ResultsPanel
from .widgets import divider


def _side_panel(object_name, width, *widgets):
    body = QWidget()
    body.setObjectName("panelBody")
    layout = QVBoxLayout(body)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    for i, w in enumerate(widgets):
        if i:
            layout.addWidget(divider())
        layout.addWidget(w)
    layout.addStretch(1)
    scroll = QScrollArea()
    scroll.setObjectName(object_name)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(body)
    scroll.setFixedWidth(width)
    return scroll


class MainWindow(QMainWindow):
    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state or AppState(parent=self)
        self.setWindowTitle("Busemann")
        self.setWindowIcon(theme.icon("busemann", "accent", 64))
        self.setMinimumSize(*tokens.MIN_WINDOW)

        self.flight_panel = FlightPanel(self.state)
        self.design_panel = DesignPanel(self.state)
        self.results_panel = ResultsPanel(self.state)
        self.left_panel = _side_panel("leftPanel", tokens.LEFT_PANEL_WIDTH,
                                      self.flight_panel, self.design_panel)
        self.right_panel = _side_panel("rightPanel", tokens.RIGHT_PANEL_WIDTH, self.results_panel)

        self.canvas = CanvasPlaceholder()
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.canvas, "Design")

        centre = QWidget()
        centre.setObjectName("canvasHost")
        row = QHBoxLayout(centre)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.left_panel)
        row.addWidget(self.tabs, 1)
        row.addWidget(self.right_panel)
        self.setCentralWidget(centre)

        self._build_toolbar()
        self._build_status_bar()

        self.state.busy_changed.connect(self.busy.setVisible)
        self.state.compute_time_changed.connect(lambda _ms: self._update_status())
        self.state.inputs_changed.connect(lambda _i: self._update_status())
        self._update_status()
        self.state.recompute_now()

    def _build_toolbar(self):
        bar = QToolBar("Main")
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(bar)
        self.toggle_left = QAction(theme.icon("panel-left", "text"), "Show inputs panel", self)
        self.toggle_left.setShortcut(QKeySequence("Ctrl+["))
        self.toggle_right = QAction(theme.icon("panel-right", "text"), "Show results panel", self)
        self.toggle_right.setShortcut(QKeySequence("Ctrl+]"))
        for action, panel in ((self.toggle_left, self.left_panel),
                              (self.toggle_right, self.right_panel)):
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(panel.setVisible)
            bar.addAction(action)

    def _build_status_bar(self):
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        self.busy = QProgressBar()
        self.busy.setObjectName("busy")
        self.busy.setRange(0, 0)
        self.busy.setTextVisible(False)
        self.busy.setFixedWidth(tokens.space(10))
        self.busy.hide()
        self.compute_label = QLabel()
        self.model_label = QLabel()
        self.units_label = QLabel()
        status.addWidget(self.compute_label)
        status.addWidget(self.busy)
        status.addPermanentWidget(self.model_label)
        status.addPermanentWidget(QLabel("·"))
        status.addPermanentWidget(self.units_label)

    def _update_status(self):
        ms = self.state.compute_ms
        self.compute_label.setText("Computing…" if ms is None else f"Computed in {ms:.0f} ms")
        self.model_label.setText(f"Ideal gas, γ = {self.state.inputs.gamma:.2f}")
        self.units_label.setText(self.state.inputs.units)

    def closeEvent(self, event):
        self.state.shutdown()
        super().closeEvent(event)


def setup_application(app):
    app.setApplicationName("Busemann")
    app.setApplicationVersion(__version__)
    theme.apply(app)
    return app


def main(argv=None):
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication.instance() or QApplication(sys.argv if argv is None else ["busemann", *argv])
    setup_application(app)
    window = MainWindow()
    window.resize(1440, 900)
    window.show()
    return app.exec()
