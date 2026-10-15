"""Isentropic flow relations for a calorically perfect gas.

All functions take Mach number M (dimensionless) and ratio of specific heats
gamma (default 1.4, air). Scalars and NumPy arrays are both accepted.
Reference: NACA Report 1135, isentropic flow relations.
"""
import numpy as np
from scipy.optimize import brentq


def _validate(M, gamma, allow_zero=True):
    M = np.asarray(M, dtype=float)
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    if allow_zero and np.any(M < 0):
        raise ValueError("Mach number must be >= 0")
    if not allow_zero and np.any(M <= 0):
        raise ValueError("Mach number must be > 0")
    return M


def stagnation_temperature_ratio(M, gamma=1.4):
    """T0/T = 1 + (gamma-1)/2 * M^2  (energy conservation, adiabatic flow)."""
    M = _validate(M, gamma)
    return 1.0 + 0.5 * (gamma - 1.0) * M**2


def stagnation_pressure_ratio(M, gamma=1.4):
    """p0/p = (T0/T)^(gamma/(gamma-1))  (isentropic)."""
    return stagnation_temperature_ratio(M, gamma) ** (gamma / (gamma - 1.0))


def stagnation_density_ratio(M, gamma=1.4):
    """rho0/rho = (T0/T)^(1/(gamma-1))  (isentropic)."""
    return stagnation_temperature_ratio(M, gamma) ** (1.0 / (gamma - 1.0))


def area_mach_ratio(M, gamma=1.4):
    """A/A* = (1/M) * [2/(gamma+1) * (1 + (gamma-1)/2 * M^2)]^((gamma+1)/(2(gamma-1)))."""
    M = _validate(M, gamma, allow_zero=False)
    base = (2.0 / (gamma + 1.0)) * (1.0 + 0.5 * (gamma - 1.0) * M**2)
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    return base**exponent / M


def mach_from_area_ratio(area_ratio, gamma=1.4, supersonic=True):
    """Invert A/A* -> M on the chosen branch using Brent's root-finding method.

    Every A/A* > 1 has two solutions: one subsonic, one supersonic.
    """
    if area_ratio < 1.0:
        raise ValueError("A/A* must be >= 1")
    if np.isclose(area_ratio, 1.0):
        return 1.0

    def f(M):
        return area_mach_ratio(M, gamma) - area_ratio

    if supersonic:
        # f(1) < 0; grow the upper bound until f > 0 so brentq has a sign change
        upper = 2.0
        while f(upper) < 0:
            upper *= 2.0
        return float(brentq(f, 1.0, upper, xtol=1e-12))
    # subsonic: A/A* -> infinity as M -> 0, so f > 0 near zero and f(1) < 0
    return float(brentq(f, 1e-8, 1.0, xtol=1e-12))