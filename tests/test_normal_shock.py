import pytest

from inletdesign import normal_shock


@pytest.mark.skip(reason="reference value not verified")
def test_mach_downstream_at_M1_equals_1():
    # At M1=1 the shock is vanishingly weak; M2 should equal 1.
    assert normal_shock.mach_downstream(1.0) == pytest.approx(1.0)


@pytest.mark.skip(reason="reference value not verified")
def test_mach_downstream_table():
    # VERIFY: NACA 1135, Table II, M1=2.0, gamma=1.4
    expected_M2 = None  # TODO: fill in from NACA 1135 Table II
    assert normal_shock.mach_downstream(2.0) == pytest.approx(expected_M2)


@pytest.mark.skip(reason="reference value not verified")
def test_pressure_ratio_at_M1_equals_1():
    assert normal_shock.pressure_ratio(1.0) == pytest.approx(1.0)


@pytest.mark.skip(reason="reference value not verified")
def test_pressure_ratio_table():
    # VERIFY: NACA 1135, Table II, M1=2.0, gamma=1.4
    expected_p2_p1 = None  # TODO: fill in from NACA 1135 Table II
    assert normal_shock.pressure_ratio(2.0) == pytest.approx(expected_p2_p1)


@pytest.mark.skip(reason="reference value not verified")
def test_temperature_ratio_table():
    # VERIFY: NACA 1135, Table II, M1=2.0, gamma=1.4
    expected_T2_T1 = None  # TODO: fill in from NACA 1135 Table II
    assert normal_shock.temperature_ratio(2.0) == pytest.approx(expected_T2_T1)


@pytest.mark.skip(reason="reference value not verified")
def test_density_ratio_table():
    # VERIFY: NACA 1135, Table II, M1=2.0, gamma=1.4
    expected_rho2_rho1 = None  # TODO: fill in from NACA 1135 Table II
    assert normal_shock.density_ratio(2.0) == pytest.approx(expected_rho2_rho1)


@pytest.mark.skip(reason="reference value not verified")
def test_stagnation_pressure_ratio_at_M1_equals_1():
    assert normal_shock.stagnation_pressure_ratio(1.0) == pytest.approx(1.0)


@pytest.mark.skip(reason="reference value not verified")
def test_stagnation_pressure_ratio_table():
    # VERIFY: NACA 1135, Table II, M1=2.0, gamma=1.4
    expected_p02_p01 = None  # TODO: fill in from NACA 1135 Table II
    assert normal_shock.stagnation_pressure_ratio(2.0) == pytest.approx(expected_p02_p01)


@pytest.mark.skip(reason="not yet implemented")
def test_raises_valueerror_for_subsonic_upstream():
    # A normal shock requires supersonic upstream flow (M1 >= 1).
    with pytest.raises(ValueError):
        normal_shock.mach_downstream(0.5)
