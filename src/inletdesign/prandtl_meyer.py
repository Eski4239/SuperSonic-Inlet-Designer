"""Prandtl-Meyer expansion relations for a calorically perfect gas.

All functions take Mach number M (dimensionless, M >= 1) and ratio of
specific heats gamma (default 1.4, air). Angles are in DEGREES at this
public API. Scalars and NumPy arrays are accepted for the closed-form
functions. Reference: NACA Report 1135, Prandtl-Meyer function.
"""
import numpy as np
from scipy.optimize import brentq


def _validate(M, gamma):
    M = np.asarray(M, dtype=float)
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    if np.any(M < 1.0):
        raise ValueError("M must be >= 1 (Prandtl-Meyer function requires supersonic flow)")
    return M


def nu(M, gamma=1.4):
    """nu(M) = sqrt((gamma+1)/(gamma-1)) * arctan(sqrt((gamma-1)/(gamma+1)*(M^2-1))) - arctan(sqrt(M^2-1))."""
    M = _validate(M, gamma)
    k = np.sqrt((gamma + 1.0) / (gamma - 1.0))
    term = np.sqrt(M**2 - 1.0)
    nu_rad = k * np.arctan(term / k) - np.arctan(term)
    return np.degrees(nu_rad)


def nu_max(gamma=1.4):
    """nu_max = 90 * (sqrt((gamma+1)/(gamma-1)) - 1) degrees, the M -> infinity limit."""
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    return 90.0 * (np.sqrt((gamma + 1.0) / (gamma - 1.0)) - 1.0)


def mach_from_nu(nu_deg, gamma=1.4):
    """Invert nu(M) for M via Brent's method on f(M) = nu(M, gamma) - nu_deg."""
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    max_nu = nu_max(gamma)
    if nu_deg < 0.0 or nu_deg >= max_nu:
        raise ValueError(f"nu must be in [0, {max_nu}) degrees for gamma={gamma}")

    def f(M):
        return nu(M, gamma) - nu_deg

    upper = 2.0
    while f(upper) < 0:
        upper *= 2.0
    return float(brentq(f, 1.0, upper, xtol=1e-12))
