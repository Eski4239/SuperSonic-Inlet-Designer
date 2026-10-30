"""Results panel (right): KPI cards and the warnings list. Region table arrives in M4."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from inletdesign import units as _units

from .. import theme
from ..theme import tokens
from ..widgets import KpiCard, section_title
from . import format as fmt


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
        self._set_warnings(self.state.warnings())

    def _set_warnings(self, warnings):
        for row in self._warning_labels:
            row.deleteLater()
        self._warning_labels = []
        for text in warnings:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(tokens.space(1))
            icon = QLabel()
            icon.setPixmap(theme.icon("alert-triangle", "warn", 16).pixmap(16, 16))
            icon.setAlignment(Qt.AlignmentFlag.AlignTop)
            label = QLabel(text[0].upper() + text[1:])
            label.setObjectName("warningRow")
            label.setWordWrap(True)
            h.addWidget(icon)
            h.addWidget(label, 1)
            self._warnings_layout.addWidget(row)
            self._warning_labels.append(row)
        self.warnings_box.setVisible(bool(warnings))

    def warning_texts(self):
        return [row.findChild(QLabel, "warningRow").text() for row in self._warning_labels]
