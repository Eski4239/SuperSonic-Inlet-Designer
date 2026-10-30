"""QApplication setup and the main window (spec 5 layout: left 300 | canvas | right 320)."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QProgressBar, QScrollArea, QTabWidget,
    QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from . import __version__
from .theme import qt as theme
from .canvas import InletCanvas
from .state import AppState
from .theme import tokens
from .views import DesignPanel, FlightPanel, ResultsPanel
from .tooltips import tip
from .views.explain_drawer import ExplainDrawer
from .views.offdesign_tab import OffDesignTab
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

        self.canvas = InletCanvas(self.state)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.canvas, "Design")
        self.offdesign_tab = OffDesignTab(self.state)
        self.tabs.addTab(self.offdesign_tab, "Off-design")
        self.tabs.currentChanged.connect(self._on_tab)

        centre = QWidget()
        centre.setObjectName("canvasHost")
        row = QHBoxLayout(centre)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.left_panel)
        row.addWidget(self.tabs, 1)
        row.addWidget(self.right_panel)
        self.setCentralWidget(centre)

        self.explain_drawer = ExplainDrawer(self.state, self)
        self._build_toolbar()
        self._build_status_bar()

        # Transitions animate on discrete changes, not while the Mach slider is dragged.
        slider = self.flight_panel.mach.slider
        slider.sliderPressed.connect(lambda: self.canvas.set_animations_enabled(False))
        slider.sliderReleased.connect(lambda: self.canvas.set_animations_enabled(True))
        for canvas in self.canvases():
            canvas.selection_changed.connect(
                lambda *sel, c=canvas: self._on_selection(c, *sel))
            canvas.picture_changed.connect(lambda c=canvas: self._on_picture(c))
        self.results_panel.station_table.row_clicked.connect(
            lambda row: self.current_canvas().select("region", row))

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
        self.toggle_left.setToolTip(tip("toolbar.toggle_left"))
        self.toggle_left.setShortcut(QKeySequence("Ctrl+["))
        self.toggle_right = QAction(theme.icon("panel-right", "text"), "Show results panel", self)
        self.toggle_right.setToolTip(tip("toolbar.toggle_right"))
        self.toggle_right.setShortcut(QKeySequence("Ctrl+]"))
        for action, panel in ((self.toggle_left, self.left_panel),
                              (self.toggle_right, self.right_panel)):
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(panel.setVisible)
            bar.addAction(action)

        bar.addSeparator()
        self.zoom_in_action = QAction(theme.icon("zoom-in", "text"), "Zoom in", self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.setToolTip(tip("toolbar.zoom_in"))
        self.zoom_in_action.triggered.connect(lambda: self.current_canvas().zoom_in())
        self.zoom_out_action = QAction(theme.icon("zoom-out", "text"), "Zoom out", self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.setToolTip(tip("toolbar.zoom_out"))
        self.zoom_out_action.triggered.connect(lambda: self.current_canvas().zoom_out())
        self.fit_action = QAction(theme.icon("maximize", "text"), "Fit drawing (F)", self)
        self.fit_action.triggered.connect(lambda: self.current_canvas().fit())
        self.fit_action.setToolTip(tip("toolbar.fit"))
        for action in (self.zoom_in_action, self.zoom_out_action, self.fit_action):
            bar.addAction(action)

        bar.addSeparator()
        self.layer_actions = {}
        for name, label, on in (("shocks", "Shocks", True), ("regions", "Regions", True),
                                ("dimensions", "Dimensions", False), ("grid", "Grid", False)):
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(on)
            action.setToolTip(tip("toolbar.layer"))
            action.toggled.connect(lambda v, n=name: self._set_layer(n, v))
            self._set_layer(name, on)
            button = QToolButton()
            button.setObjectName("layerToggle")
            button.setDefaultAction(action)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            bar.addWidget(button)
            self.layer_actions[name] = action

        bar.addSeparator()
        self.explain_action = QAction("Explain", self)
        self.explain_action.setCheckable(True)
        self.explain_action.setToolTip(tip("toolbar.explain"))
        self.explain_action.toggled.connect(self._toggle_explain)
        self.explain_drawer.close_button.clicked.connect(
            lambda: self.explain_action.setChecked(False))
        button = QToolButton()
        button.setObjectName("layerToggle")
        button.setDefaultAction(self.explain_action)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        bar.addWidget(button)

    def canvases(self):
        return (self.canvas, self.offdesign_tab.canvas)

    def current_canvas(self):
        return self.offdesign_tab.canvas if self.tabs.currentWidget() is self.offdesign_tab             else self.canvas

    def _set_layer(self, name, visible):
        for canvas in self.canvases():
            canvas.set_layer_visible(name, visible)

    def _on_tab(self, _index):
        view = "offdesign" if self.tabs.currentWidget() is self.offdesign_tab else "design"
        self.state.set_active_view(view)
        canvas = self.current_canvas()
        self.results_panel.station_table.set_regions(canvas.region_states())
        self.results_panel.show_selection(*canvas.selection, canvas.payload(*canvas.selection))
        if self.explain_drawer.is_open:
            self.explain_drawer.show_item(*canvas.selection)

    def _on_selection(self, canvas, kind, index, payload):
        """Results panel, station table and Explain drawer follow the visible tab's canvas."""
        if canvas is self.current_canvas():
            self.results_panel.show_selection(kind, index, payload)
            if self.explain_drawer.is_open:
                self.explain_drawer.show_item(kind, index)

    def _toggle_explain(self, on):
        if on:
            self.explain_drawer.show_item(*self.current_canvas().selection)
            self.explain_drawer.open()
        else:
            self.explain_drawer.close_drawer()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.explain_drawer.place()

    def _on_picture(self, canvas):
        if canvas is self.current_canvas():
            self.results_panel.station_table.set_regions(canvas.region_states())
            self.results_panel.station_table.select_row(
                canvas.selection[1] if canvas.selection[0] == "region" else None)

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
        separator = QLabel("·")
        for label, key in ((self.compute_label, "status.compute"),
                           (self.model_label, "status.model"),
                           (self.units_label, "status.units"), (separator, "status.sep")):
            label.setToolTip(tip(key))
        status.addWidget(self.compute_label)
        status.addWidget(self.busy)
        status.addPermanentWidget(self.model_label)
        status.addPermanentWidget(separator)
        status.addPermanentWidget(self.units_label)

    def _update_status(self):
        s = self.state
        if s.compute_ms is None:
            text = "Computing…"
        else:
            design = "design cached" if s.compute_cached else f"design {s.design_ms:.0f} ms"
            sweep = f" · sweep {s.sweep_ms:.0f} ms" if s.sweep_ms is not None else ""
            text = design + sweep
        self.compute_label.setText(text)
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


def setup_high_dpi():
    """Fractional Windows display scaling (125 %, 150 %) as-is: PassThrough rounding.
    Must run before the QApplication is created."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)


def main(argv=None):
    setup_high_dpi()
    app = QApplication.instance() or QApplication(sys.argv if argv is None else ["busemann", *argv])
    setup_application(app)
    window = MainWindow()
    window.resize(1440, 900)
    window.show()
    return app.exec()
