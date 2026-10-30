"""Off-design evaluation of a FIXED inlet geometry at a different freestream Mach.

build_geometry()/design_inlet() in geometry.py design a shock-on-lip inlet for
one Mach number. This module evaluates that same fixed geometry (same ramp
angles, ramp corner points, lip position) at a different M_inf, where the
ramp shocks generally no longer land exactly on the cowl lip.
"""
from dataclasses import dataclass

import numpy as np

from . import inlet as _inlet
from .geometry import cowl_check
from . import oblique_shock as obl

SUBSONIC_WARNING = "flow subsonic behind last ramp shock; no terminal normal shock"


@dataclass(frozen=True)
class OffDesignResult:
    M_inf: float
    regime: str
    dx_over_hc: list
    mass_capture_ratio: float
    recovery_oblique: float
    M_duct: float
    recovery_total: float
    warnings: list
    betas_deg: list = None            # off-design ramp shock angles (relative to local flow)
    capture_streamline: list = None   # [(x, y), ...] upstream end first, ending at the lip
    cowl_angle_deg: float = None
    theta_max_freestream_deg: float = None
    cowl_margin_deg: float = None     # theta_max(M_inf) - cowl angle; < 0: cowl shock detached


def _side_of_line(point, origin, angle_deg):
    d = np.array([np.cos(np.radians(angle_deg)), np.sin(np.radians(angle_deg))])
    normal = np.array([-d[1], d[0]])
    return np.dot(point - origin, normal)


def _segment_intersection(p1, d1, p2, d2):
    """Intersection of two rays p1+t*d1 and p2+s*d2. Returns (point, t, s) or None if parallel."""
    A = np.array([d1, -d2]).T
    b = p2 - p1
    det = A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0]
    if abs(det) < 1e-15:
        return None
    t, s = np.linalg.solve(A, b)
    return p1 + t * d1, t, s


def off_design(geom, M_inf, gamma=1.4):
    """Evaluate a fixed inlet geometry (ramp angles/corners/lip unchanged) at a new M_inf.

    If the flow behind the last ramp shock is subsonic (possible just above
    detachment), no terminal normal shock is applied: recovery_total equals
    recovery_oblique, M_duct is that subsonic Mach number, and a warning is added.

    Raises:
        ValueError: if any ramp shock detaches at the new M_inf
            (message contains "shock detached").
    """
    h_c = geom.capture_height
    ramp_angles = geom.ramp_angles_deg
    ramp_points = geom.ramp_points
    lip = np.array(geom.lip)
    n = len(ramp_angles)
    warnings = []

    phis = [0.0]
    M = M_inf
    betas = []
    for i, theta in enumerate(ramp_angles):
        try:
            state = obl.oblique_shock_state(M, theta, gamma, weak=True)
        except ValueError as exc:
            theta_max, _ = obl.max_deflection(M, gamma)
            raise ValueError(
                f"shock detached at ramp {i}: theta={theta} deg, theta_max={theta_max:.4f} deg"
            ) from exc
        betas.append(state["beta"])
        M = state["M2"]
        phis.append(phis[-1] + theta)
    M_duct = M

    dx_list = []
    cross_points = []
    for i in range(n):
        origin = np.array(ramp_points[i])
        angle = np.radians(phis[i] + betas[i])
        d = np.array([np.cos(angle), np.sin(angle)])
        t = (h_c - origin[1]) / d[1]
        x_cross = origin[0] + t * d[0]
        cross_points.append((x_cross, h_c, t))
        dx_list.append((x_cross - lip[0]) / h_c)

    tol = 1e-6 * h_c

    for i in range(n - 1):
        origin_i = np.array(ramp_points[i])
        angle_i = np.radians(phis[i] + betas[i])
        d_i = np.array([np.cos(angle_i), np.sin(angle_i)])
        origin_j = np.array(ramp_points[i + 1])
        angle_j = np.radians(phis[i + 1] + betas[i + 1])
        d_j = np.array([np.cos(angle_j), np.sin(angle_j)])
        result = _segment_intersection(origin_i, d_i, origin_j, d_j)
        if result is not None:
            point, t, s = result
            t_max_i = cross_points[i][2]
            t_max_j = cross_points[i + 1][2]
            if 0 <= t <= t_max_i and 0 <= s <= t_max_j and point[1] < h_c - tol:
                warnings.append(
                    "shocks merge before cowl line; merged-shock regime not modelled"
                )

    first_dx = dx_list[0]
    if first_dx < -tol:
        regime = "spillage"
    elif first_dx > tol:
        regime = "shock-in-duct"
    else:
        regime = "on-lip"

    ref_point = np.array([ramp_points[0][0] - 10.0 * h_c, ramp_points[0][1] + 0.01 * h_c])

    crossed_shocks = []
    for i in range(n):
        origin = np.array(ramp_points[i])
        shock_angle = phis[i] + betas[i]
        ref_side = _side_of_line(ref_point, origin, shock_angle)
        lip_side = _side_of_line(lip, origin, shock_angle)
        if abs(lip_side) < tol:
            continue
        if np.sign(ref_side) != np.sign(lip_side):
            crossed_shocks.append(i)

    streamline = [tuple(float(c) for c in lip)]
    if not crossed_shocks:
        mass_capture_ratio = 1.0
    else:
        point = lip.copy()
        for i in sorted(crossed_shocks, reverse=True):
            region_dir = np.radians(phis[i + 1] + 180.0)
            d = np.array([np.cos(region_dir), np.sin(region_dir)])
            origin = np.array(ramp_points[i])
            shock_angle = np.radians(phis[i] + betas[i])
            ds = np.array([np.cos(shock_angle), np.sin(shock_angle)])
            result = _segment_intersection(point, d, origin, ds)
            point = result[0]
            streamline.append(tuple(float(c) for c in point))
        mass_capture_ratio = point[1] / h_c

    ramp_states = _inlet.compress_ramps(M_inf, ramp_angles, gamma)
    recovery_oblique = ramp_states[-1].p0_ratio if n > 0 else 1.0
    if M_duct < 1.0:
        # Just above detachment the weak-branch solution can be subsonic: there
        # is no terminal normal shock, so the obliques set the whole recovery.
        recovery_total = recovery_oblique
        warnings.append(SUBSONIC_WARNING)
    else:
        recovery_total = _inlet.compress(M_inf, ramp_angles, gamma)[-1].p0_ratio

    if regime == "shock-in-duct":
        warnings.append("internal reflected shock not modelled; recovery is an upper bound")

    cowl_angle = float(sum(ramp_angles))
    theta_max_inf, cowl_margin, _, cowl_message = cowl_check(M_inf, cowl_angle, gamma)
    if cowl_message:
        warnings.append(cowl_message)

    return OffDesignResult(
        M_inf=M_inf,
        regime=regime,
        dx_over_hc=dx_list,
        mass_capture_ratio=mass_capture_ratio,
        recovery_oblique=recovery_oblique,
        M_duct=M_duct,
        recovery_total=recovery_total,
        warnings=warnings,
        betas_deg=[float(b) for b in betas],
        capture_streamline=streamline[::-1],
        cowl_angle_deg=cowl_angle,
        theta_max_freestream_deg=float(theta_max_inf),
        cowl_margin_deg=float(cowl_margin),
    )
