"""Normal shock relations for a calorically perfect gas.

All functions take the upstream Mach number M1 (dimensionless, M1 >= 1) and
the ratio of specific heats gamma (dimensionless, default 1.4 for air).
Governing relations come from one-dimensional normal shock theory (e.g.
NACA Report 1135, Table II / Eqs. 53-59), derived from conservation of mass,
momentum, and energy across a stationary normal shock.

A normal shock requires M1 >= 1 (supersonic upstream flow); callers should
raise ValueError for M1 < 1 once implemented.
"""


def mach_downstream(M1, gamma=1.4):
    """Downstream Mach number M2 behind a normal shock.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        M2 (dimensionless, M2 <= 1)
    Governing equation (in words):
        M2 squared equals [1 plus (gamma-1)/2 times M1 squared] divided by
        [gamma times M1 squared minus (gamma-1)/2]. This comes from jointly
        solving the normal-shock mass, momentum, and energy jump conditions.
    Raises:
        ValueError: if M1 < 1 (normal shock requires supersonic upstream flow).
    """
    raise NotImplementedError


def pressure_ratio(M1, gamma=1.4):
    """Static pressure ratio across a normal shock, p2/p1.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        p2/p1 (dimensionless, >= 1)
    Governing equation (in words):
        p2/p1 equals 1 plus [2*gamma/(gamma+1)] times (M1 squared minus 1).
        This follows directly from the momentum (Rankine-Hugoniot) jump
        condition across the shock.
    Raises:
        ValueError: if M1 < 1.
    """
    raise NotImplementedError


def temperature_ratio(M1, gamma=1.4):
    """Static temperature ratio across a normal shock, T2/T1.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        T2/T1 (dimensionless, >= 1)
    Governing equation (in words):
        T2/T1 equals (p2/p1) times (rho1/rho2), i.e. the product of the
        pressure ratio and the inverse density ratio, consistent with the
        ideal gas law applied on both sides of the shock.
    Raises:
        ValueError: if M1 < 1.
    """
    raise NotImplementedError


def density_ratio(M1, gamma=1.4):
    """Density ratio across a normal shock, rho2/rho1.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        rho2/rho1 (dimensionless, >= 1, approaching (gamma+1)/(gamma-1) as
        M1 -> infinity)
    Governing equation (in words):
        rho2/rho1 equals [(gamma+1) times M1 squared] divided by
        [(gamma-1) times M1 squared plus 2]. This follows from the mass
        (continuity) jump condition combined with the momentum relation.
    Raises:
        ValueError: if M1 < 1.
    """
    raise NotImplementedError


def stagnation_pressure_ratio(M1, gamma=1.4):
    """Stagnation (total) pressure ratio across a normal shock, p02/p01.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        p02/p01 (dimensionless, <= 1; equals 1 only at M1 = 1)
    Governing equation (in words):
        p02/p01 is the product of the density ratio raised to the power
        gamma/(gamma-1) and the inverse pressure ratio raised to the power
        1/(gamma-1), reflecting the entropy increase (total pressure loss)
        across the irreversible shock while total temperature is conserved.
    Raises:
        ValueError: if M1 < 1.
    """
    raise NotImplementedError
