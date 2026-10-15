import math

import pytest

from inletdesign import oblique_shock


@pytest.mark.skip(reason="reference value not verified")
def test_deflection_angle_table():
    # VERIFY: NACA 1135 theta-beta-M chart, M1=2.0, beta=40deg, gamma=1.4
    M1 = 2.0
    beta = math.radians(40.0)
    expected_theta = None  # TODO: fill in from NACA 1135 chart
    assert oblique_shock.deflection_angle(M1, beta) == pytest.approx(expected_theta)


@pytest.mark.skip(reason="reference value not verified")
def test_shock_angle_weak_root_table():
    # VERIFY: NACA 1135 theta-beta-M chart, M1=2.0, theta=10deg (weak), gamma=1.4
    M1 = 2.0
    theta = math.radians(10.0)
    expected_beta = None  # TODO: fill in from NACA 1135 chart
    assert oblique_shock.shock_angle(M1, theta, weak=True) == pytest.approx(expected_beta)


@pytest.mark.skip(reason="reference value not verified")
def test_shock_angle_strong_root_table():
    # VERIFY: NACA 1135 theta-beta-M chart, M1=2.0, theta=10deg (strong), gamma=1.4
    M1 = 2.0
    theta = math.radians(10.0)
    expected_beta = None  # TODO: fill in from NACA 1135 chart
    assert oblique_shock.shock_angle(M1, theta, weak=False) == pytest.approx(expected_beta)


@pytest.mark.skip(reason="reference value not verified")
def test_max_deflection_angle_table():
    # VERIFY: NACA 1135 theta-beta-M chart, M1=2.0, gamma=1.4 (theta_max)
    M1 = 2.0
    expected_theta_max = None  # TODO: fill in from NACA 1135 chart
    assert oblique_shock.max_deflection_angle(M1) == pytest.approx(expected_theta_max)


@pytest.mark.skip(reason="reference value not verified")
def test_post_shock_state_table():
    # VERIFY: NACA 1135 theta-beta-M chart + Table II combination, M1=2.0, beta=40deg
    M1 = 2.0
    beta = math.radians(40.0)
    expected_state = None  # TODO: fill in dict of expected M2, p2_p1, T2_T1, rho2_rho1, p02_p01
    assert oblique_shock.post_shock_state(M1, beta) == expected_state


@pytest.mark.skip(reason="not yet implemented")
def test_shock_angle_raises_for_detached_shock():
    # A deflection angle greater than theta_max has no attached-shock
    # solution; the shock detaches and shock_angle must raise ValueError.
    M1 = 2.0
    theta_too_large = math.radians(89.0)
    with pytest.raises(ValueError):
        oblique_shock.shock_angle(M1, theta_too_large)
