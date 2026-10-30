"""U.S. Standard Atmosphere 1976, 0-86 km geometric altitude.

Seven layers of linear temperature in geopotential altitude H, hydrostatic
pressure, ideal-gas density. Inputs are geometric altitude z in metres;
scalars and NumPy arrays are both accepted.

Temperature returned is the molecular-scale temperature T_M. Below 80 km it
equals the kinetic temperature; between 80 and 86 km the 1976 standard
applies a molecular-weight correction of less than 0.05 %, not modelled here.

Reference: U.S. Standard Atmosphere 1976 (NOAA-S/T 76-1562).
"""
import numpy as np

G0 = 9.80665                 # m/s^2, standard gravity
R_STAR = 8314.32             # J/(kmol K), universal gas constant (1976 value)
M0 = 28.9644                 # kg/kmol, sea-level mean molecular weight
R_AIR = R_STAR / M0          # J/(kg K)
R_EARTH = 6356766.0          # m, effective Earth radius
GAMMA = 1.4
SUTHERLAND_BETA = 1.458e-6   # kg/(m s K^0.5)
SUTHERLAND_S = 110.4         # K

Z_MAX = 86000.0              # m, geometric

# Layer bases: geopotential altitude (m) and lapse rate (K/m) above each base.
_H_BASE = np.array([0.0, 11000.0, 20000.0, 32000.0, 47000.0, 51000.0, 71000.0])
_LAPSE = np.array([-0.0065, 0.0, 0.001, 0.0028, 0.0, -0.0028, -0.002])
_T0 = 288.15
_P0 = 101325.0


def _base_states():
    T = [_T0]
    p = [_P0]
    for i in range(len(_H_BASE) - 1):
        dH = _H_BASE[i + 1] - _H_BASE[i]
        Tb, pb, L = T[-1], p[-1], _LAPSE[i]
        T_top = Tb + L * dH
        if L == 0.0:
            p_top = pb * np.exp(-G0 * dH / (R_AIR * Tb))
        else:
            p_top = pb * (Tb / T_top) ** (G0 / (R_AIR * L))
        T.append(T_top)
        p.append(p_top)
    return np.array(T), np.array(p)


_T_BASE, _P_BASE = _base_states()


def _validate(z):
    z = np.asarray(z, dtype=float)
    if np.any(~np.isfinite(z)):
        raise ValueError("altitude must be finite")
    if np.any(z < 0.0) or np.any(z > Z_MAX):
        raise ValueError(f"altitude must be within 0-{Z_MAX:.0f} m (geometric)")
    return z


def geopotential_altitude(z):
    """H = r0 z / (r0 + z)  (geometric -> geopotential, r0 = 6 356 766 m)."""
    z = _validate(z)
    return R_EARTH * z / (R_EARTH + z)


def geometric_altitude(H):
    """z = r0 H / (r0 - H)  (inverse of geopotential_altitude)."""
    H = np.asarray(H, dtype=float)
    return R_EARTH * H / (R_EARTH - H)


def temperature(z):
    """T = T_b + L_b (H - H_b) in the layer containing H."""
    H = geopotential_altitude(z)
    i = np.clip(np.searchsorted(_H_BASE, H, side="right") - 1, 0, len(_H_BASE) - 1)
    return _T_BASE[i] + _LAPSE[i] * (H - _H_BASE[i])


def pressure(z):
    """p = p_b (T_b/T)^(g0/(R L_b))  (L_b != 0);  p = p_b exp(-g0 (H-H_b)/(R T_b))  (L_b = 0)."""
    H = geopotential_altitude(z)
    i = np.clip(np.searchsorted(_H_BASE, H, side="right") - 1, 0, len(_H_BASE) - 1)
    Tb, pb, L, Hb = _T_BASE[i], _P_BASE[i], _LAPSE[i], _H_BASE[i]
    T = Tb + L * (H - Hb)
    isothermal = L == 0.0
    safe_L = np.where(isothermal, 1.0, L)
    p_grad = pb * (Tb / T) ** (G0 / (R_AIR * safe_L))
    p_iso = pb * np.exp(-G0 * (H - Hb) / (R_AIR * Tb))
    return np.where(isothermal, p_iso, p_grad)


def density(z):
    """rho = p / (R T)  (ideal gas)."""
    return pressure(z) / (R_AIR * temperature(z))


def speed_of_sound(z):
    """a = sqrt(gamma R T)."""
    return np.sqrt(GAMMA * R_AIR * temperature(z))


def dynamic_viscosity(T):
    """mu = beta T^1.5 / (T + S)  (Sutherland's law, beta = 1.458e-6, S = 110.4 K)."""
    T = np.asarray(T, dtype=float)
    if np.any(T <= 0.0):
        raise ValueError("temperature must be > 0 K")
    return SUTHERLAND_BETA * T**1.5 / (T + SUTHERLAND_S)
