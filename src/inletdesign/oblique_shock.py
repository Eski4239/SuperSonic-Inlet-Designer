"""Oblique shock relations for a calorically perfect gas.

All functions take Mach numbers (dimensionless) and angles in radians unless
otherwise noted, plus the ratio of specific heats gamma (dimensionless,
default 1.4 for air). Governing relations come from two-dimensional oblique
shock theory (e.g. NACA Report 1135, Eqs. 122-130 and the theta-beta-M
chart), obtained by applying normal-shock relations to the velocity
component normal to the shock, M1 * sin(beta).
"""


def deflection_angle(M1, beta, gamma=1.4):
    """Flow deflection angle theta produced by a given shock angle beta.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        beta: oblique shock angle relative to the upstream flow (radians)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        theta: flow deflection angle (radians)
    Governing equation (in words):
        tan(theta) equals 2*cot(beta) times [M1 squared * sin(beta) squared
        minus 1] divided by [M1 squared * (gamma + cos(2*beta)) plus 2].
        This is the theta-beta-M relation, derived by applying normal-shock
        jump conditions to the shock-normal Mach number component M1*sin(beta)
        and resolving velocities into shock-tangential and shock-normal parts.
    """
    raise NotImplementedError


def shock_angle(M1, theta, gamma=1.4, weak=True):
    """Shock angle beta for a given upstream Mach number and deflection angle.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        theta: flow deflection angle (radians, 0 <= theta <= theta_max(M1))
        gamma: ratio of specific heats cp/cv (dimensionless)
        weak: if True, return the weak-shock solution (smaller beta); if
            False, return the strong-shock solution (larger beta). The
            theta-beta-M relation has two valid roots for beta (plus the
            trivial Mach-wave root) when theta < theta_max.
    Output:
        beta: oblique shock angle (radians)
    Governing equation (in words):
        Invert the theta-beta-M relation (see deflection_angle) for beta
        given M1 and theta, typically via iterative root-finding, selecting
        the weak or strong root as requested.
    Raises:
        ValueError: if theta exceeds max_deflection_angle(M1, gamma), since
            no attached oblique shock solution exists (the shock detaches).
    """
    raise NotImplementedError


def max_deflection_angle(M1, gamma=1.4):
    """Maximum flow deflection angle theta_max for a given upstream Mach number.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        theta_max (radians): the largest deflection angle for which an
        attached oblique shock solution exists at this M1. Deflections
        beyond this angle cause the shock to detach from the surface and
        form a curved, detached bow shock.
    Governing equation (in words):
        theta_max is the value of theta at the point where d(theta)/d(beta)
        equals zero on the theta-beta-M curve for the given M1, found by
        maximizing the deflection_angle relation over beta.
    """
    raise NotImplementedError


def post_shock_state(M1, beta, gamma=1.4):
    """Full post-shock flow state for an oblique shock of angle beta.

    Inputs:
        M1: upstream Mach number (dimensionless, M1 >= 1)
        beta: oblique shock angle relative to the upstream flow (radians)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        A mapping (e.g. dict) with keys:
            "M2": downstream Mach number (dimensionless)
            "p2_p1": static pressure ratio (dimensionless)
            "T2_T1": static temperature ratio (dimensionless)
            "rho2_rho1": density ratio (dimensionless)
            "p02_p01": stagnation pressure ratio (dimensionless)
            "theta": flow deflection angle (radians)
    Governing equation (in words):
        Decompose the upstream Mach number into shock-normal component
        M1n = M1*sin(beta), apply the normal_shock relations to M1n to get
        M2n and the ratios, then recover M2 by recombining M2n with the
        unchanged shock-tangential velocity component via
        M2 = M2n / sin(beta - theta).
    """
    raise NotImplementedError
