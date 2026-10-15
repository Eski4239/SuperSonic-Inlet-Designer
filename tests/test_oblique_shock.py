import numpy as np
import pytest

from inletdesign import isentropic as isen
from inletdesign import normal_shock as ns
from inletdesign import oblique_shock as obl


@pytest.mark.parametrize("M1", [1.5, 2.0, 3.0, 5.0])
def test_theta_zero_gives_mach_angle(M1):
    mach_angle = np.degrees(np.arcsin(1.0 / M1))
    assert obl.beta_from_theta(M1, 0.0) == pytest.approx(mach_angle, rel=1e-6)


@pytest.mark.parametrize("M1", [1.5, 2.0, 3.0, 5.0])
def test_beta_90_matches_normal_shock(M1):
    assert obl.theta_from_beta(M1, 90.0) == pytest.approx(0.0, abs=1e-8)

    state = obl.oblique_shock_state(M1, 1e-6, weak=False)
    assert state["beta"] == pytest.approx(90.0, abs=1e-3)
    assert state["M2"] == pytest.approx(ns.mach_downstream(M1), rel=1e-4)
    assert state["p2_p1"] == pytest.approx(ns.pressure_ratio(M1), rel=1e-4)
    assert state["T2_T1"] == pytest.approx(ns.temperature_ratio(M1), rel=1e-4)
    assert state["rho2_rho1"] == pytest.approx(ns.density_ratio(M1), rel=1e-4)
    assert state["p02_p01"] == pytest.approx(ns.stagnation_pressure_ratio(M1), rel=1e-4)


@pytest.mark.parametrize("M1, beta", [(2.0, 50.0), (3.0, 40.0), (5.0, 20.0)])
def test_round_trip_beta_theta_beta(M1, beta):
    theta = obl.theta_from_beta(M1, beta)
    recovered = obl.beta_from_theta(M1, theta, weak=True)
    assert recovered == pytest.approx(beta, rel=1e-6)


@pytest.mark.parametrize("M1, theta", [(2.0, 10.0), (3.0, 15.0), (5.0, 10.0)])
def test_stagnation_pressure_ratio_less_than_one(M1, theta):
    state = obl.oblique_shock_state(M1, theta)
    assert state["p02_p01"] < 1.0


@pytest.mark.parametrize("M1, theta", [(2.0, 10.0), (3.0, 15.0), (5.0, 10.0)])
def test_total_temperature_conserved(M1, theta):
    state = obl.oblique_shock_state(M1, theta)
    M2 = state["M2"]
    T0_T1 = isen.stagnation_temperature_ratio(M1)
    T0_T2 = isen.stagnation_temperature_ratio(M2)
    assert T0_T1 == pytest.approx(T0_T2 * state["T2_T1"], rel=1e-6)


# VERIFY against NACA 1135 (user-supplied, gamma=1.4, M1=2.0, theta=10deg weak; pending confirmation)
def test_naca_1135_cross_check_M1_2_theta_10_weak():
    state = obl.oblique_shock_state(2.0, 10.0, weak=True)
    assert state["beta"] == pytest.approx(39.31, rel=1e-3)
    assert state["M2"] == pytest.approx(1.641, rel=1e-3)
    assert state["p2_p1"] == pytest.approx(1.707, rel=1e-3)


# VERIFY against NACA 1135 (user-supplied, gamma=1.4, M1=2.0; pending confirmation)
def test_naca_1135_max_deflection_M1_2():
    theta_max, _ = obl.max_deflection(2.0)
    assert theta_max == pytest.approx(22.97, rel=1e-3)


def test_beta_from_theta_raises_for_detached_shock():
    with pytest.raises(ValueError):
        obl.beta_from_theta(2.0, 40.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        obl.theta_from_beta(0.5, 20.0)
    with pytest.raises(ValueError):
        obl.beta_from_theta(2.0, 10.0, gamma=1.0)
