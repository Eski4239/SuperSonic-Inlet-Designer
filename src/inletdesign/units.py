"""SI <-> imperial display-unit conversion.

All core quantities are SI. Each quantity has one display unit per system;
every conversion is a pure scale factor (display = SI * factor), so there are
no offsets (temperatures are absolute: K and degrees Rankine).

Exact definitions: 1 ft = 0.3048 m, 1 in = 0.0254 m, 1 lbm = 0.45359237 kg,
1 lbf = 1 lbm * 9.80665 m/s^2, 1 degR = 1/1.8 K.
"""
import numpy as np

FT = 0.3048
INCH = 0.0254
LBM = 0.45359237
LBF = LBM * 9.80665
PSI = LBF / INCH**2

SYSTEMS = ("SI", "Imperial")

# quantity -> {system: (label, display units per SI unit)}
_UNITS = {
    "altitude": {"SI": ("km", 1e-3), "Imperial": ("ft", 1.0 / FT)},
    "length": {"SI": ("m", 1.0), "Imperial": ("in", 1.0 / INCH)},
    "pressure": {"SI": ("kPa", 1e-3), "Imperial": ("psi", 1.0 / PSI)},
    "temperature": {"SI": ("K", 1.0), "Imperial": ("°R", 1.8)},
    "density": {"SI": ("kg/m³", 1.0), "Imperial": ("lbm/ft³", FT**3 / LBM)},
    "velocity": {"SI": ("m/s", 1.0), "Imperial": ("ft/s", 1.0 / FT)},
    "mass_flow_per_span": {"SI": ("kg/s/m", 1.0), "Imperial": ("lbm/s/ft", FT / LBM)},
    "per_length": {"SI": ("1/m", 1.0), "Imperial": ("1/ft", FT)},
    "viscosity": {"SI": ("Pa·s", 1.0), "Imperial": ("lbf·s/ft²", FT**2 / LBF)},
}

QUANTITIES = tuple(_UNITS)


def _lookup(quantity, system):
    if system not in SYSTEMS:
        raise ValueError(f"unit system must be one of {SYSTEMS}, got {system!r}")
    if quantity not in _UNITS:
        raise ValueError(f"unknown quantity {quantity!r}; known: {QUANTITIES}")
    return _UNITS[quantity][system]


def unit_label(quantity, system):
    """Display unit label, e.g. unit_label('pressure', 'SI') -> 'kPa'."""
    return _lookup(quantity, system)[0]


def to_display(value_si, quantity, system):
    """display = SI * factor."""
    factor = _lookup(quantity, system)[1]
    value = np.asarray(value_si, dtype=float) * factor
    return float(value) if value.ndim == 0 else value


def from_display(value, quantity, system):
    """SI = display / factor."""
    factor = _lookup(quantity, system)[1]
    value = np.asarray(value, dtype=float) / factor
    return float(value) if value.ndim == 0 else value
