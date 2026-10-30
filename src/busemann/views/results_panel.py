"""Results panel (right): KPI cards, warnings, and the canvas selection. Region table in M4."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from inletdesign import units as _units

from .. import theme
from ..theme import tokens
from ..widgets import KpiCard, section_title
from . import format as fmt
from .rows import region_rows, shock_rows

SELECTION_HINT = "Click a region or shock on the canvas to inspect it."


class ResultsPanel(QWidget):
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state

        self.cards = {
            "recovery_total": KpiCard(
                "Total pressure recovery",
                "p0 after the terminal normal shock / p0∞, incl. all oblique shocks (dimensionless)."),
            "recovery_oblique": KpiCard(
                "Oblique-only recovery",
                "p0 behind the last ramp shock / p0∞, before the terminal shock (dimensionless)."),
            "M_duct": KpiCard("Duct Mach number",
                              "Mach number entering the subsonic duct (dimensionless)."),
            "mass_capture": KpiCard("Mass capture",
                                    "Captured / ideal mass flow A0/Ac (dimensionless)."),
            "mass_flow": KpiCard("Captured mass flow",
                                 "ρ∞ V∞ h_c (A0/Ac), per unit span."),
        }

        self.warnings_box = QFrame()
        self.warnings_box.setObjectName("warningsBox")
        self._warnings_layout = QVBoxLayout(self.warnings_box)
        self._warnings_layout.setContentsMargins(tokens.space(1) + 4, tokens.space(1),
                                                 tokens.space(1) + 4, tokens.space(1))
        self._warnings_layout.setSpacing(tokens.space(1) // 2)
        self.warnings_box.hide()
        self._warning_labels = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(tokens.space(2), tokens.space(2), tokens.space(2), tokens.space(2))
        layout.setSpacing(tokens.space(1))
        layout.addWidget(section_title("Results"))
        for card in self.cards.values():
            layout.addWidget(card)
        layout.addSpacing(tokens.space(1))
        layout.addWidget(self.warnings_box)
        layout.addSpacing(tokens.space(1))
        layout.addWidget(section_title("Selection"))
        self.selection_title = QLabel(SELECTION_HINT)
        self.selection_title.setObjectName("selectionHint")
        self.selection_title.setWordWrap(True)
        self.selection_box = QWidget()
        self._selection_grid = QGridLayout(self.selection_box)
        self._selection_grid.setContentsMargins(0, 0, 0, 0)
        self._selection_grid.setHorizontalSpacing(tokens.space(1))
        self._selection_grid.setVerticalSpacing(4)
        self._selection_grid.setColumnStretch(1, 1)
        self._selection_widgets = []
        self.selection_values = {}
        self._selection = (None, None, None)
        layout.addWidget(self.selection_title)
        layout.addWidget(self.selection_box)
        layout.addStretch(1)

        state.design_ready.connect(lambda *_: self.refresh())
        state.freestream_ready.connect(lambda *_: self.refresh())
        state.inputs_changed.connect(lambda *_: self.refresh())
        self.refresh()

    def refresh(self):
        d = self.state.design
        system = self.state.inputs.units
        if d is None:
            for card in self.cards.values():
                card.clear()
        else:
            subsonic = d.M_duct < 1.0 and not any(r.beta_deg == 90.0 for r in d.regions)
            self.cards["recovery_total"].set_value(
                f"{d.recovery_total:.4f}", "p0/p0∞",
                "no terminal shock (subsonic)" if subsonic else "incl. terminal normal shock")
            self.cards["recovery_total"].set_badge("constrained" if d.constrained else None)
            self.cards["recovery_total"].badge.setToolTip(
                f"Oswatitsch optimum limited to a cowl angle of "
                f"{d.inputs.max_cowl_angle_deg or 0:.1f} deg" if d.constrained else "")
            self.cards["recovery_oblique"].set_value(
                f"{d.recovery_oblique:.4f}", "p0/p0∞", f"{d.inputs.n_ramps} oblique shock(s)")
            self.cards["M_duct"].set_value(f"{d.M_duct:.3f}", "",
                                           "behind last ramp shock" if subsonic
                                           else "behind terminal normal shock")
            self.cards["mass_capture"].set_value(f"{d.mass_capture:.3f}", "A0/Ac",
                                                 "shock-on-lip design point")
        mdot = self.state.captured_mass_flow()
        if mdot is None:
            self.cards["mass_flow"].clear()
        else:
            self.cards["mass_flow"].set_value(
                fmt.sig(_units.to_display(mdot, "mass_flow_per_span", system), 4),
                _units.unit_label("mass_flow_per_span", system))
        self._set_warnings(self.state.notices())
        if self._selection[0] is not None:       # dimensional values follow the unit system
            self.show_selection(*self._selection)

    def _set_warnings(self, notices):
        """notices: [(level, text)]; "error" rows use the error colour and icon."""
        for row in self._warning_labels:
            row.deleteLater()
        self._warning_labels = []
        any_error = any(level == "error" for level, _ in notices)
        self.warnings_box.setProperty("level", "error" if any_error else "warn")
        self.warnings_box.style().unpolish(self.warnings_box)
        self.warnings_box.style().polish(self.warnings_box)
        warnings = notices
        for level, text in warnings:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(tokens.space(1))
            icon = QLabel()
            icon.setPixmap(theme.icon("alert-triangle", "error" if level == "error" else "warn",
                                      16).pixmap(16, 16))
            icon.setAlignment(Qt.AlignmentFlag.AlignTop)
            label = QLabel(fmt.nbsp(text[0].upper() + text[1:]))
            label.setObjectName("errorRow" if level == "error" else "warningRow")
            label.setProperty("level", level)
            label.setWordWrap(True)
            h.addWidget(icon)
            h.addWidget(label, 1)
            self._warnings_layout.addWidget(row)
            self._warning_labels.append(row)
        self.warnings_box.setVisible(bool(warnings))

    # --- canvas selection ------------------------------------------------------------------
    def show_selection(self, kind, index, payload):
        self._selection = (kind, index, payload)
        for w in self._selection_widgets:
            w.deleteLater()
        self._selection_widgets = []
        self.selection_values = {}
        if kind is None or payload is None:
            self.selection_title.setObjectName("selectionHint")
            self.selection_title.setText(SELECTION_HINT)
            self._repolish(self.selection_title)
            return
        if kind == "region":
            rows = region_rows(payload, self.state.freestream, self.state.inputs.units)
        else:
            rows = shock_rows(payload)
        self.selection_title.setObjectName("hoverTitle")
        self.selection_title.setText(payload.name[:1].upper() + payload.name[1:])
        self._repolish(self.selection_title)
        for r, (key, label, value, text, unit) in enumerate(rows):
            self.selection_values[key] = value
            name = QLabel(label)
            name.setObjectName("readoutLabel")
            val = QLabel(text)
            val.setObjectName("readoutValue")
            val.setFont(theme.mono_font())
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            un = QLabel(unit)
            un.setObjectName("readoutUnit")
            un.setFont(theme.mono_font(tokens.SIZE_LABEL))
            un.setMinimumWidth(tokens.space(7))
            for c, w in enumerate((name, val, un)):
                self._selection_grid.addWidget(w, r, c)
                self._selection_widgets.append(w)

    @staticmethod
    def _repolish(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def warning_texts(self):
        return [self._row_label(row).text().replace("\u00a0", " ")
                for row in self._warning_labels]

    def warning_levels(self):
        return [self._row_label(row).property("level") for row in self._warning_labels]

    @staticmethod
    def _row_label(row):
        return row.findChild(QLabel, "warningRow") or row.findChild(QLabel, "errorRow")
