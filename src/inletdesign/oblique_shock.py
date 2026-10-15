"""Oblique shock relations for a calorically perfect gas.

All functions take the upstream Mach number M1 (dimensionless, M1 >= 1) and
ratio of specific heats gamma (default 1.4, air). Angles are in DEGREES at
this public API (converted to radians internally). Oblique shock states are
obtained by decomposing the flow into the shock-normal Mach number
Mn1 = M1*sin(beta) and reusing the normal_shock relations on that component.
Reference: NACA Report 1135, oblique shock relations (theta-beta-M chart).
Notation: theta = flow deflection, beta = shock angle (NACA 1135 uses the reverse).
"""
import numpy as np
from scipy.optimize import brentq, minimize_scalar

from . import normal_shock as ns


def _validate(M1, gamma):
    M1 = np.asarray(M1, dtype=float)
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    if np.any(M1 < 1.0):
        raise ValueError("M1 must be >= 1 (oblique shock requires supersonic upstream flow)")
    return M1


def _mach_angle_deg(M1):
    return np.degrees(np.arcsin(1.0 / M1))


def theta_from_beta(M1, beta_deg, gamma=1.4):
    """theta-beta-M relation: tan(theta) = 2*cot(beta)*(M1^2*sin(beta)^2 - 1) / (M1^2*(gamma+cos(2*beta)) + 2)."""
    M1 = _validate(M1, gamma)
    beta = np.radians(beta_deg)
    numerator = M1**2 * np.sin(beta) ** 2 - 1.0
    denominator = M1**2 * (gamma + np.cos(2.0 * beta)) + 2.0
    tan_theta = 2.0 / np.tan(beta) * numerator / denominator
    return np.degrees(np.arctan(tan_theta))


def max_deflection(M1, gamma=1.4):
    """theta_max and the beta at which it occurs, found by maximizing theta_from_beta over beta."""
    M1 = _validate(M1, gamma)
    mach_angle = float(_mach_angle_deg(M1))

    def neg_theta(beta_deg):
        return -theta_from_beta(M1, beta_deg, gamma)

    result = minimize_scalar(
        neg_theta, bounds=(mach_angle + 1e-9, 90.0 - 1e-9), method="bounded"
    )
    beta_at_max = float(result.x)
    theta_max = float(-result.fun)
    return theta_max, beta_at_max


def beta_from_theta(M1, theta_deg, gamma=1.4, weak=True):
    """Invert the theta-beta-M relation for beta, selecting the weak or strong root."""
    M1 = _validate(M1, gamma)
    theta_max, beta_at_max = max_deflection(M1, gamma)
    if theta_deg > theta_max:
        raise ValueError(
            f"theta={theta_deg} deg exceeds theta_max={theta_max:.4f} deg for M1={float(M1)}: "
            "shock detaches, no attached oblique shock solution exists"
        )
    mach_angle = float(_mach_angle_deg(M1))
    if theta_deg <= 0.0:
        return mach_angle if weak else 90.0

    def f(beta_deg):
        return theta_from_beta(M1, beta_deg, gamma) - theta_deg

    if weak:
        return brentq(f, mach_angle, beta_at_max, xtol=1e-10)
    return brentq(f, beta_at_max, 90.0, xtol=1e-10)


def oblique_shock_state(M1, theta_deg, gamma=1.4, weak=True):
    """Full post-shock state for the oblique shock solving the given deflection theta.

    Returns a dict with keys: beta, M2, p2_p1, T2_T1, rho2_rho1, p02_p01
    (beta in degrees). Computed by applying normal_shock relations to the
    shock-normal Mach number Mn1 = M1*sin(beta), then recovering M2 via
    M2 = Mn2 / sin(beta - theta).
    """
    beta_deg = beta_from_theta(M1, theta_deg, gamma, weak)
    beta = np.radians(beta_deg)
    Mn1 = M1 * np.sin(beta)
    Mn2 = ns.mach_downstream(Mn1, gamma)
    p2_p1 = ns.pressure_ratio(Mn1, gamma)
    T2_T1 = ns.temperature_ratio(Mn1, gamma)
    rho2_rho1 = ns.density_ratio(Mn1, gamma)
    p02_p01 = ns.stagnation_pressure_ratio(Mn1, gamma)
    M2 = Mn2 / np.sin(np.radians(beta_deg - theta_deg))
    return {
        "beta": float(beta_deg),
        "M2": float(M2),
        "p2_p1": float(p2_p1),
        "T2_T1": float(T2_T1),
        "rho2_rho1": float(rho2_rho1),
        "p02_p01": float(p02_p01),
    }
