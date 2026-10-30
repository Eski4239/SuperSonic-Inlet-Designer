"""External-compression inlet modeling: chains ramp oblique shocks and a
terminal normal shock, reusing oblique_shock.py and normal_shock.py.
"""
from .flowstate import FlowState
from . import normal_shock as ns
from . import oblique_shock as obl


def compress_ramps(M_inf, ramp_angles_deg, gamma=1.4):
    """Compress freestream flow through the N oblique ramp shocks only.

    Same convention as compress() (incremental ramp angles, ratios relative to
    freestream), but without the terminal normal shock. Returns one FlowState
    per ramp shock; the flow after the last one may be subsonic.

    Raises:
        ValueError: if any oblique shock would detach.
    """
    states = []
    M = M_inf
    p_ratio = 1.0
    T_ratio = 1.0
    p0_ratio = 1.0

    for i, theta_deg in enumerate(ramp_angles_deg):
        try:
            result = obl.oblique_shock_state(M, theta_deg, gamma=gamma, weak=True)
        except ValueError as exc:
            raise ValueError(f"ramp {i} (theta={theta_deg} deg, M={M}): {exc}") from exc
        M = result["M2"]
        p_ratio *= result["p2_p1"]
        T_ratio *= result["T2_T1"]
        p0_ratio *= result["p02_p01"]
        states.append(
            FlowState(M=M, p_ratio=p_ratio, T_ratio=T_ratio, p0_ratio=p0_ratio, T0_ratio=1.0)
        )
    return states


def compress(M_inf, ramp_angles_deg, gamma=1.4):
    """Compress freestream flow through N oblique ramp shocks + a terminal normal shock.

    Each entry in ramp_angles_deg is the incremental flow deflection introduced
    at that ramp, relative to the flow immediately upstream of it (i.e. the
    result of the previous ramp, or freestream for the first ramp). Returns
    one FlowState per shock (oblique ramps, then the terminal normal shock) —
    not including the initial freestream state. The last entry's p0_ratio is
    the overall total pressure recovery of the inlet.

    Raises:
        ValueError: if any oblique shock would detach, or if the flow is
            subsonic entering the terminal normal shock.
    """
    states = compress_ramps(M_inf, ramp_angles_deg, gamma)
    if states:
        last = states[-1]
        M, p_ratio, T_ratio, p0_ratio = last.M, last.p_ratio, last.T_ratio, last.p0_ratio
    else:
        M, p_ratio, T_ratio, p0_ratio = M_inf, 1.0, 1.0, 1.0

    M2 = ns.mach_downstream(M, gamma=gamma)
    p_ratio *= ns.pressure_ratio(M, gamma=gamma)
    T_ratio *= ns.temperature_ratio(M, gamma=gamma)
    p0_ratio *= ns.stagnation_pressure_ratio(M, gamma=gamma)
    states.append(
        FlowState(M=M2, p_ratio=p_ratio, T_ratio=T_ratio, p0_ratio=p0_ratio, T0_ratio=1.0)
    )
    return states
