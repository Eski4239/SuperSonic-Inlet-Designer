"""Read-out rows for a flow region or a shock, shared by the canvas hover card and the
results panel selection: (key, label, raw value, formatted text, unit)."""
from inletdesign import units as _units

from . import format as fmt


def region_rows(st, fs, system):
    """Hover/selection rows for a RegionState: (key, label, raw value, text, unit)."""
    rows = [
        ("M", "M", st.M, f"{st.M:.4f}", ""),
        ("p_ratio", "p/p∞", st.p_ratio, fmt.sig(st.p_ratio, 4), ""),
        ("T_ratio", "T/T∞", st.T_ratio, fmt.sig(st.T_ratio, 4), ""),
        ("p0_ratio", "p0/p0∞", st.p0_ratio, f"{st.p0_ratio:.4f}", ""),
        ("flow_angle", "Flow angle", st.theta_deg, f"{st.theta_deg:.2f}", "deg"),
    ]
    if fs is not None:
        p, T = st.p_ratio * fs.p, st.T_ratio * fs.T
        rows += [
            ("p", "p", p, fmt.sig(_units.to_display(p, "pressure", system), 4),
             _units.unit_label("pressure", system)),
            ("T", "T", T, fmt.sig(_units.to_display(T, "temperature", system), 4),
             _units.unit_label("temperature", system)),
        ]
    return rows


def shock_rows(sh):
    return [
        ("beta", "β", sh.beta_deg, f"{sh.beta_deg:.2f}", "deg"),
        ("theta", "θ", sh.theta_deg, f"{sh.theta_deg:.2f}", "deg"),
        ("M1", "M1", sh.M1, f"{sh.M1:.4f}", ""),
        ("Mn1", "M_n1", sh.Mn1, f"{sh.Mn1:.4f}", ""),
        ("p2_p1", "p2/p1", sh.p2_p1, fmt.sig(sh.p2_p1, 4), ""),
        ("p0_loss", "p0 loss", sh.p0_loss, f"{100.0 * sh.p0_loss:.2f}", "%"),
    ]
