"""Prandtl-Meyer expansion relations for a calorically perfect gas.

All functions take the ratio of specific heats gamma (dimensionless, default
1.4 for air). Governing relations come from steady, isentropic, supersonic
expansion-fan theory (e.g. NACA Report 1135, Eq. 131 / Table III).
"""


def nu(M, gamma=1.4):
    """Prandtl-Meyer function value for a given Mach number.

    Inputs:
        M: Mach number (dimensionless, M >= 1)
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        nu(M) (radians): the angle through which a supersonic flow must turn,
        starting from M=1, to reach Mach number M via an isentropic
        expansion.
    Governing equation (in words):
        nu(M) equals sqrt[(gamma+1)/(gamma-1)] times arctan(sqrt[(gamma-1)/
        (gamma+1) * (M squared - 1)]) minus arctan(sqrt(M squared - 1)).
        This is obtained by integrating the differential relation between
        flow-turning angle and Mach number along a simple-wave (isentropic,
        irrotational) expansion.
    Raises:
        ValueError: if M < 1 (the Prandtl-Meyer function is only defined for
            supersonic flow).
    """
    raise NotImplementedError


def mach_from_nu(nu_value, gamma=1.4):
    """Invert the Prandtl-Meyer function to find Mach number from nu.

    Inputs:
        nu_value: Prandtl-Meyer angle (radians, 0 <= nu_value < nu_max(gamma),
            where nu_max = (pi/2) * [sqrt((gamma+1)/(gamma-1)) - 1])
        gamma: ratio of specific heats cp/cv (dimensionless)
    Output:
        M (dimensionless, M >= 1)
    Governing equation (in words):
        Solve nu(M, gamma) == nu_value for M (see nu()), typically via
        iterative root-finding since the relation is not explicitly
        invertible in closed form.
    Raises:
        ValueError: if nu_value is negative or exceeds the maximum
            attainable value nu_max(gamma) (corresponding to M -> infinity).
    """
    raise NotImplementedError
