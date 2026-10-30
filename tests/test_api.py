import json
import math
import time

import pytest

from inletdesign import api
from inletdesign import atmosphere as atm
from inletdesign import inlet as _inlet
from inletdesign import isentropic as isen
from inletdesign.geometry import design_inlet
from inletdesign.offdesign import off_design


def _json_ok(obj):
    json.dumps(obj.to_dict())


# --- freestream -------------------------------------------------------------

def test_freestream_altitude_matches_atmosphere():
    fs = api.freestream(2.0, altitude_m=11000.0)
    assert fs.mode == "altitude"
    assert fs.p == pytest.approx(float(atm.pressure(11000.0)))
    assert fs.T == pytest.approx(float(atm.temperature(11000.0)))
    assert fs.rho == pytest.approx(fs.p / (atm.R_AIR * fs.T))
    assert fs.V == pytest.approx(2.0 * math.sqrt(1.4 * atm.R_AIR * fs.T))
    assert fs.p0 / fs.p == pytest.approx(float(isen.stagnation_pressure_ratio(2.0)))
    assert fs.T0 / fs.T == pytest.approx(float(isen.stagnation_temperature_ratio(2.0)))
    assert fs.Re_per_m == pytest.approx(fs.rho * fs.V / fs.mu)
    _json_ok(fs)


def test_freestream_manual_mode():
    fs = api.freestream(3.0, p=10000.0, T=220.0)
    assert fs.mode == "manual" and fs.altitude_m is None
    assert fs.p == 10000.0 and fs.T == 220.0
    _json_ok(fs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"p": 1e4},
        {"altitude_m": 1000.0, "p": 1e4, "T": 200.0},
        {"p": -1.0, "T": 200.0},
        {"p": 1e4, "T": 0.0},
        {"altitude_m": 90000.0},
        {"altitude_m": 0.0, "gamma": 1.0},
    ],
)
def test_freestream_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        api.freestream(2.0, **kwargs)


def test_real_gas_warning_threshold_is_on_T0():
    hot = api.freestream(6.7, altitude_m=31000.0)
    cool = api.freestream(3.2, altitude_m=24000.0)
    assert hot.T0 > api.REAL_GAS_T0_LIMIT and any("real-gas" in w for w in hot.warnings)
    assert cool.T0 < api.REAL_GAS_T0_LIMIT and not cool.warnings


def test_captured_mass_flow_closed_form():
    fs = api.freestream(3.0, p=10000.0, T=220.0)
    assert api.captured_mass_flow(fs, 0.1, 0.9) == pytest.approx(fs.rho * fs.V * 0.1 * 0.9)


# --- design -----------------------------------------------------------------

@pytest.mark.parametrize("M, n", [(3.0, 2), (2.0, 1), (4.0, 3), (2.5, 0), (3.0, 4)])
def test_design_matches_core(M, n):
    r = api.design(M, n, capture_height=0.1)
    geom = design_inlet(M, n, capture_height=0.1)
    states = _inlet.compress(M, geom.ramp_angles_deg)
    assert r.ramp_angles_deg == pytest.approx(geom.ramp_angles_deg)
    assert r.recovery_total == pytest.approx(states[-1].p0_ratio)
    assert r.M_duct == pytest.approx(states[-1].M)
    assert r.throat_height == pytest.approx(geom.throat_height)
    assert r.cowl_angle_deg == pytest.approx(geom.cowl_angle_deg)
    assert len(r.regions) == n + 2  # freestream, n ramp regions, duct
    assert r.regions[0].p0_ratio == 1.0
    assert r.regions[-1].p0_ratio == pytest.approx(r.recovery_total)
    assert r.inputs.method == "oswatitsch"
    assert not r.warnings
    _json_ok(r)


def test_design_custom_angles_round_trip():
    ref = api.design(3.0, 2)
    r = api.design(3.0, 2, ramp_angles=list(ref.ramp_angles_deg))
    assert r.inputs.method == "custom"
    assert r.recovery_total == pytest.approx(ref.recovery_total)


def test_design_custom_detached_message():
    with pytest.raises(ValueError, match="detachment limit"):
        api.design(2.0, 1, ramp_angles=[30.0])


@pytest.mark.parametrize(
    "args, kwargs",
    [
        ((0.9, 2), {}),
        ((3.0, 5), {}),
        ((3.0, 2), {"capture_height": 0.0}),
        ((3.0, 2), {"ramp_angles": [10.0]}),
        ((3.0, 2), {"ramp_angles": [10.0, -1.0]}),
    ],
)
def test_design_invalid_inputs(args, kwargs):
    with pytest.raises(ValueError):
        api.design(*args, **kwargs)


def test_design_custom_subsonic_behind_last_ramp():
    # Find the subsonic band just below detachment for one ramp at M 2 (closed-form check).
    from inletdesign import oblique_shock as obl

    theta_max, _ = obl.max_deflection(2.0)
    theta = float(theta_max) - 1e-3
    M2 = obl.oblique_shock_state(2.0, theta, weak=True)["M2"]
    assert M2 < 1.0  # weak branch is subsonic this close to theta_max
    r = api.design(2.0, 1, ramp_angles=[theta])
    assert api.SUBSONIC_WARNING in r.warnings
    assert r.recovery_total == r.recovery_oblique
    assert r.M_duct == pytest.approx(M2)


# --- off-design -------------------------------------------------------------

def test_off_design_point_matches_core():
    d = api.design(3.0, 2, capture_height=0.1)
    p = api.off_design_point(d, 2.75)
    ref = off_design(design_inlet(3.0, 2, capture_height=0.1), 2.75)
    assert p.mass_capture_ratio == pytest.approx(ref.mass_capture_ratio)
    assert p.recovery_total == pytest.approx(ref.recovery_total)
    assert p.regime == ref.regime
    _json_ok(p)


def test_off_design_point_detached_message():
    d = api.design(3.0, 2)
    with pytest.raises(ValueError, match="shock detached"):
        api.off_design_point(d, 1.5)


def test_sweep_detachment_brackets_first_attached_point():
    d = api.design(3.0, 2)
    sweep = api.off_design_sweep(d, 2.0, 3.5, 61)
    _json_ok(sweep)
    first = next(i for i, p in enumerate(sweep.points) if p is not None)
    assert first > 0
    assert sweep.machs[first - 1] < sweep.detachment_mach <= sweep.machs[first]
    assert all(p is None for p in sweep.points[:first])
    assert all(p is not None for p in sweep.points[first:])


def test_sweep_invalid_inputs():
    d = api.design(3.0, 2)
    with pytest.raises(ValueError):
        api.off_design_sweep(d, 3.0, 2.0, 10)
    with pytest.raises(ValueError):
        api.off_design_sweep(d, 2.0, 3.0, 1)


def test_sweep_performance_100_points():
    d = api.design(3.0, 2)
    t0 = time.perf_counter()
    api.off_design_sweep(d, 2.0, 4.5, 100)
    assert time.perf_counter() - t0 < 0.5
