"""Normal shock relations for a calorically perfect gas.

All functions take the upstream Mach number M1 (dimensionless, M1 >= 1) and
ratio of specific heats gamma (default 1.4, air). Scalars and NumPy arrays
are both accepted. Reference: NACA Report 1135, normal shock relations
(Eqs. 53-59).
"""
import numpy as np


def _validate(M1, gamma):
    if gamma <= 1.0:
        raise ValueError("gamma must be > 1")
    if isinstance(M1, (int, float)):  # fast path for scalars (optimiser inner loop)
        if not M1 >= 1.0:
            raise ValueError("M1 must be >= 1 (normal shock requires supersonic upstream flow)")
        return float(M1)
    M1 = np.asarray(M1, dtype=float)
    if np.any(M1 < 1.0):
        raise ValueError("M1 must be >= 1 (normal shock requires supersonic upstream flow)")
    return M1


def mach_downstream(M1, gamma=1.4):
    """M2^2 = (1 + (gamma-1)/2 * M1^2) / (gamma*M1^2 - (gamma-1)/2)."""
    M1 = _validate(M1, gamma)
    numerator = 1.0 + 0.5 * (gamma - 1.0) * M1**2
    denominator = gamma * M1**2 - 0.5 * (gamma - 1.0)
    return np.sqrt(numerator / denominator)


def pressure_ratio(M1, gamma=1.4):
    """p2/p1 = 1 + 2*gamma/(gamma+1) * (M1^2 - 1)  (momentum/Rankine-Hugoniot)."""
    M1 = _validate(M1, gamma)
    return 1.0 + (2.0 * gamma / (gamma + 1.0)) * (M1**2 - 1.0)


def density_ratio(M1, gamma=1.4):
    """rho2/rho1 = (gamma+1)*M1^2 / ((gamma-1)*M1^2 + 2)  (continuity)."""
    M1 = _validate(M1, gamma)
    return ((gamma + 1.0) * M1**2) / ((gamma - 1.0) * M1**2 + 2.0)


def temperature_ratio(M1, gamma=1.4):
    """T2/T1 = (p2/p1) / (rho2/rho1)  (ideal gas law)."""
    return pressure_ratio(M1, gamma) / density_ratio(M1, gamma)


def stagnation_pressure_ratio(M1, gamma=1.4):
    """p02/p01 = (rho2/rho1)^(gamma/(gamma-1)) * (p2/p1)^(-1/(gamma-1))  (entropy change)."""
    rho_ratio = density_ratio(M1, gamma)
    p_ratio = pressure_ratio(M1, gamma)
    return rho_ratio ** (gamma / (gamma - 1.0)) * p_ratio ** (-1.0 / (gamma - 1.0))
