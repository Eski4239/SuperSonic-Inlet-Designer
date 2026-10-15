"""Isentropic flow relations for a calorically perfect gas.

All functions take the local Mach number M (dimensionless) and the ratio of
specific heats gamma (dimensionless, default 1.4 for air) and return the
indicated dimensionless ratio. Governing relations come from one-dimensional
isentropic flow theory (e.g. NACA Report 1135, Table I / Eqs. 44-47).
"""


def stagnation_temperature_ratio(M, gamma=1.4):
    """Ratio of stagnation to static temperature, T0/T.

    Inputs:
        M: Mach number (dimensionless, M >= 0)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        T0/T (dimensionless)
    Governing equation (in words):
        T0/T equals one plus (gamma minus one) over two, times M squared.
        This follows from conservation of energy for adiabatic flow of a
        calorically perfect gas, relating static and stagnation temperature
        through the local kinetic energy per unit mass.
    """
    raise NotImplementedError


def stagnation_pressure_ratio(M, gamma=1.4):
    """Ratio of stagnation to static pressure, p0/p.

    Inputs:
        M: Mach number (dimensionless, M >= 0)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        p0/p (dimensionless)
    Governing equation (in words):
        p0/p equals the stagnation temperature ratio (T0/T) raised to the
        power gamma/(gamma minus one). This follows from combining the
        isentropic relation between pressure and temperature (p proportional
        to T^(gamma/(gamma-1))) with the energy-derived temperature ratio.
    """
    raise NotImplementedError


def stagnation_density_ratio(M, gamma=1.4):
    """Ratio of stagnation to static density, rho0/rho.

    Inputs:
        M: Mach number (dimensionless, M >= 0)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        rho0/rho (dimensionless)
    Governing equation (in words):
        rho0/rho equals the stagnation temperature ratio (T0/T) raised to
        the power 1/(gamma minus one). This follows from the isentropic
        relation between density and temperature (rho proportional to
        T^(1/(gamma-1))) combined with the energy-derived temperature ratio.
    """
    raise NotImplementedError


def area_mach_ratio(M, gamma=1.4):
    """Ratio of local duct area to sonic (throat) area, A/A*.

    Inputs:
        M: Mach number (dimensionless, M > 0)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        A/A* (dimensionless, >= 1)
    Governing equation (in words):
        A/A* is derived from mass continuity between a point at Mach M and
        the sonic throat (M=1), expressed using the isentropic stagnation
        density and temperature ratios: A/A* equals (1/M) times the ratio of
        [one plus (gamma-1)/2 times M squared] to [one plus (gamma-1)/2],
        raised to the power (gamma+1)/(2*(gamma-1)).
    """
    raise NotImplementedError


def mach_from_area_ratio(area_ratio, gamma=1.4, supersonic=True):
    """Invert the area-Mach relation to find M given A/A*.

    Inputs:
        area_ratio: A/A* (dimensionless, >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
        supersonic: if True, return the supersonic (M > 1) root; if False,
            return the subsonic (M < 1) root. The area-Mach relation is
            two-to-one (except at A/A*=1), so this flag selects the branch.
    Output:
        M (dimensionless)
    Governing equation (in words):
        Solve area_mach_ratio(M, gamma) == area_ratio for M on the requested
        branch, typically via iterative root-finding since the relation is
        not explicitly invertible in closed form.
    """
    raise NotImplementedError
