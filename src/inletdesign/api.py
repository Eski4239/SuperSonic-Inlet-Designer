"""Stable facade over the inletdesign core for applications (GUI, future web).

Every result is a frozen dataclass of plain Python floats, ints, strings and
tuples (no numpy types), so `to_dict()` output is JSON-serialisable. Invalid
input raises ValueError with a message meant to be shown to a user.

Conventions: SI units, angles in degrees, ramp angles incremental (as in
inlet.compress), flow angles cumulative from the freestream direction.
"""
import dataclasses
import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import atmosphere as _atm
from . import inlet as _inlet
from . import isentropic as _isen
from . import oblique_shock as _obl
from . import offdesign as _off
from .geometry import build_geometry, design_inlet

REAL_GAS_T0_LIMIT = 800.0  # K; above this, vibrational excitation makes constant gamma questionable
SUBSONIC_WARNING = _off.SUBSONIC_WARNING
METHODS = ("oswatitsch", "custom")


class _Serialisable:
    def to_dict(self):
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class Freestream(_Serialisable):
    M: float
    gamma: float
    mode: str            # "altitude" or "manual"
    altitude_m: float    # None in manual mode
    p: float             # Pa
    T: float             # K
    rho: float           # kg/m^3
    a: float             # m/s
    V: float             # m/s
    p0: float            # Pa
    T0: float            # K
    mu: float            # Pa s
    Re_per_m: float      # 1/m
    warnings: tuple


@dataclass(frozen=True)
class RegionState(_Serialisable):
    name: str
    theta_deg: float     # cumulative flow angle
    beta_deg: float      # angle of the shock entering this region (None for freestream)
    M: float
    p_ratio: float       # p / p_inf
    T_ratio: float       # T / T_inf
    p0_ratio: float      # p0 / p0_inf


@dataclass(frozen=True)
class DesignInputs(_Serialisable):
    M: float
    n_ramps: int
    method: str
    ramp_angles_deg: tuple   # custom angles, or () for oswatitsch
    capture_height: float
    gamma: float


@dataclass(frozen=True)
class DesignGeometry(_Serialisable):
    ramp_points: tuple       # ((x, y), ...) including the terminal-shock foot
    lip: tuple
    shocks: tuple            # ((start, end), ...); the last one is the terminal normal shock


@dataclass(frozen=True)
class DesignResult(_Serialisable):
    inputs: DesignInputs
    ramp_angles_deg: tuple
    flow_angles_deg: tuple   # cumulative, starting with 0 (freestream)
    betas_deg: tuple
    regions: tuple           # RegionState, freestream first
    recovery_oblique: float
    recovery_total: float
    M_duct: float
    throat_height: float
    cowl_angle_deg: float
    mass_capture: float
    geometry: DesignGeometry
    warnings: tuple


@dataclass(frozen=True)
class OffDesignResult(_Serialisable):
    M_inf: float
    regime: str
    dx_over_hc: tuple
    mass_capture_ratio: float
    recovery_oblique: float
    M_duct: float
    recovery_total: float
    warnings: tuple


@dataclass(frozen=True)
class Sweep(_Serialisable):
    machs: tuple
    points: tuple            # OffDesignResult, or None where a shock detached
    detachment_mach: float   # lowest M_inf with all ramp shocks attached


def _f(x):
    return None if x is None else float(x)


def _pt(p):
    return (float(p[0]), float(p[1]))


def _check_mach(M, minimum=1.0):
    if not isinstance(M, (int, float)) or not math.isfinite(M):
        raise ValueError("Mach number must be a finite number")
    if M <= minimum:
        raise ValueError(f"Mach number must be > {minimum:g} (got {M:g})")


def _check_gamma(gamma):
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError(f"gamma must be > 1 (got {gamma:g})")


def freestream(M, altitude_m=None, p=None, T=None, gamma=1.4):
    """Dimensional freestream from Mach and either altitude (USSA-1976) or manual p, T.

    V = M a, a = sqrt(gamma R T), p0 = p (p0/p), T0 = T (T0/T), Re/m = rho V / mu (Sutherland).
    """
    _check_mach(M, minimum=0.0)
    _check_gamma(gamma)
    if altitude_m is not None and (p is not None or T is not None):
        raise ValueError("give either an altitude or a manual p and T, not both")
    if altitude_m is not None:
        mode = "altitude"
        p = float(_atm.pressure(altitude_m))
        T = float(_atm.temperature(altitude_m))
        altitude_m = float(altitude_m)
    else:
        if p is None or T is None:
            raise ValueError("give an altitude, or both a manual pressure and temperature")
        if not p > 0:
            raise ValueError(f"pressure must be > 0 Pa (got {p:g})")
        if not T > 0:
            raise ValueError(f"temperature must be > 0 K (got {T:g})")
        mode = "manual"
        p, T = float(p), float(T)

    R = _atm.R_AIR
    rho = p / (R * T)
    a = math.sqrt(gamma * R * T)
    V = M * a
    T0 = T * float(_isen.stagnation_temperature_ratio(M, gamma))
    p0 = p * float(_isen.stagnation_pressure_ratio(M, gamma))
    mu = float(_atm.dynamic_viscosity(T))

    warnings = []
    if T0 > REAL_GAS_T0_LIMIT:
        warnings.append(
            f"real-gas regime: T0 = {T0:.0f} K > {REAL_GAS_T0_LIMIT:.0f} K; "
            "vibrational excitation makes the ideal-gas (constant gamma) model optimistic"
        )

    return Freestream(
        M=float(M), gamma=float(gamma), mode=mode, altitude_m=altitude_m, p=p, T=T,
        rho=rho, a=a, V=V, p0=p0, T0=T0, mu=mu, Re_per_m=rho * V / mu,
        warnings=tuple(warnings),
    )


def captured_mass_flow(fs, capture_height, mass_capture=1.0):
    """mdot' = rho V h_c (A0/Ac)  (kg/s per metre span)."""
    return fs.rho * fs.V * capture_height * mass_capture


def _validate_custom_angles(M, n_ramps, ramp_angles, gamma):
    angles = tuple(float(a) for a in ramp_angles)
    if len(angles) != n_ramps:
        raise ValueError(f"expected {n_ramps} ramp angles, got {len(angles)}")
    Mi = M
    for i, theta in enumerate(angles):
        if not math.isfinite(theta) or theta <= 0:
            raise ValueError(f"ramp {i + 1}: angle must be > 0 deg (got {theta:g})")
        theta_max, _ = _obl.max_deflection(Mi, gamma)
        if theta >= theta_max:
            raise ValueError(
                f"ramp {i + 1}: {theta:.2f} deg exceeds the detachment limit "
                f"{float(theta_max):.2f} deg at M = {Mi:.3f}"
            )
        Mi = _obl.oblique_shock_state(Mi, theta, gamma, weak=True)["M2"]
        if Mi <= 1.0 and i < n_ramps - 1:
            raise ValueError(
                f"flow is subsonic (M = {Mi:.3f}) behind ramp {i + 1}; "
                "no further ramp shocks are possible"
            )
    return angles


@lru_cache(maxsize=256)
def _design_cached(M, n_ramps, capture_height, gamma, ramp_angles):
    if ramp_angles is None:
        method = "oswatitsch"
        geom = design_inlet(M, n_ramps, capture_height=capture_height, gamma=gamma)
    else:
        method = "custom"
        try:
            geom = build_geometry(M, list(ramp_angles), capture_height, gamma=gamma)
        except ValueError as exc:
            raise ValueError(f"infeasible ramp layout: {exc}") from exc

    angles = tuple(float(a) for a in geom.ramp_angles_deg)
    betas = tuple(float(b) for b in geom.betas_deg)
    flow = [0.0]
    for a in angles:
        flow.append(flow[-1] + a)

    warnings = []
    ramp_states = _inlet.compress_ramps(M, list(angles), gamma)
    regions = [RegionState("freestream", 0.0, None, float(M), 1.0, 1.0, 1.0)]
    for i, s in enumerate(ramp_states):
        regions.append(
            RegionState(f"behind shock {i + 1}", flow[i + 1], betas[i],
                        float(s.M), float(s.p_ratio), float(s.T_ratio), float(s.p0_ratio))
        )
    recovery_oblique = float(ramp_states[-1].p0_ratio) if ramp_states else 1.0
    M_before_terminal = float(ramp_states[-1].M) if ramp_states else float(M)

    if M_before_terminal < 1.0:
        warnings.append(SUBSONIC_WARNING)
        recovery_total = recovery_oblique
        M_duct = M_before_terminal
    else:
        terminal = _inlet.compress(M, list(angles), gamma)[-1]
        recovery_total = float(terminal.p0_ratio)
        M_duct = float(terminal.M)
        regions.append(
            RegionState("duct (behind normal shock)", flow[-1], 90.0, M_duct,
                        float(terminal.p_ratio), float(terminal.T_ratio), recovery_total)
        )

    geometry = DesignGeometry(
        ramp_points=tuple(_pt(p) for p in geom.ramp_points),
        lip=_pt(geom.lip),
        shocks=tuple((_pt(a), _pt(b)) for a, b in geom.shocks),
    )
    inputs = DesignInputs(
        M=float(M), n_ramps=int(n_ramps), method=method,
        ramp_angles_deg=() if ramp_angles is None else angles,
        capture_height=float(capture_height), gamma=float(gamma),
    )
    return DesignResult(
        inputs=inputs, ramp_angles_deg=angles, flow_angles_deg=tuple(flow), betas_deg=betas,
        regions=tuple(regions), recovery_oblique=recovery_oblique,
        recovery_total=recovery_total, M_duct=M_duct,
        throat_height=float(geom.throat_height), cowl_angle_deg=float(geom.cowl_angle_deg),
        mass_capture=1.0, geometry=geometry, warnings=tuple(warnings),
    )


def design(M, n_ramps, capture_height=0.1, gamma=1.4, ramp_angles=None):
    """Shock-on-lip design at Mach M.

    ramp_angles=None uses the Oswatitsch equal-strength optimum; otherwise the
    given incremental ramp angles (one per ramp) are checked against detachment
    and used directly. Results are cached on the inputs.
    """
    _check_mach(M)
    _check_gamma(gamma)
    if not isinstance(n_ramps, int) or not 0 <= n_ramps <= 4:
        raise ValueError(f"number of ramps must be an integer 0-4 (got {n_ramps!r})")
    if not math.isfinite(capture_height) or capture_height <= 0:
        raise ValueError(f"capture height must be > 0 (got {capture_height:g})")
    angles = None
    if ramp_angles is not None:
        angles = _validate_custom_angles(M, n_ramps, ramp_angles, gamma)
    return _design_cached(float(M), n_ramps, float(capture_height), float(gamma), angles)


def _geometry_of(design_result):
    i = design_result.inputs
    return build_geometry(i.M, list(design_result.ramp_angles_deg), i.capture_height,
                          gamma=i.gamma)


def _convert_off(r):
    return OffDesignResult(
        M_inf=float(r.M_inf), regime=r.regime,
        dx_over_hc=tuple(float(d) for d in r.dx_over_hc),
        mass_capture_ratio=float(r.mass_capture_ratio),
        recovery_oblique=float(r.recovery_oblique), M_duct=float(r.M_duct),
        recovery_total=float(r.recovery_total), warnings=tuple(r.warnings),
    )


def off_design_point(design_result, M):
    """Evaluate the frozen design geometry at freestream Mach M.

    Raises ValueError (message contains "shock detached") if a ramp shock detaches.
    """
    _check_mach(M)
    return _convert_off(_off.off_design(_geometry_of(design_result), float(M),
                                        design_result.inputs.gamma))


def _attached(design_result, M):
    gamma = design_result.inputs.gamma
    Mi = M
    for theta in design_result.ramp_angles_deg:
        if Mi <= 1.0:  # subsonic ahead of a further ramp: no attached shock possible
            return False
        theta_max, _ = _obl.max_deflection(Mi, gamma)
        if theta >= theta_max:
            return False
        Mi = _obl.oblique_shock_state(Mi, theta, gamma, weak=True)["M2"]
    return True  # subsonic behind the LAST ramp is allowed (no terminal shock)


def detachment_mach(design_result, tol=1e-5):
    """Lowest M_inf (to tol) at which every ramp shock of the design is attached (bisection)."""
    lo, hi = 1.0 + 1e-9, design_result.inputs.M
    if _attached(design_result, lo):
        return 1.0
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if _attached(design_result, mid):
            hi = mid
        else:
            lo = mid
    return float(hi)


def off_design_sweep(design_result, M_min, M_max, n):
    """Evaluate n equally spaced Mach numbers in [M_min, M_max]; None where detached."""
    _check_mach(M_min)
    if not M_max > M_min:
        raise ValueError("M_max must be greater than M_min")
    if not isinstance(n, int) or n < 2:
        raise ValueError("n must be an integer >= 2")
    geom = _geometry_of(design_result)
    gamma = design_result.inputs.gamma
    machs = tuple(float(m) for m in np.linspace(M_min, M_max, n))
    points = []
    for M in machs:
        try:
            points.append(_convert_off(_off.off_design(geom, M, gamma)))
        except ValueError as exc:
            if "shock detached" not in str(exc):
                raise
            points.append(None)
    return Sweep(machs=machs, points=tuple(points), detachment_mach=detachment_mach(design_result))
