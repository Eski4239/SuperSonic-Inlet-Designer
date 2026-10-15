import pytest

from inletdesign import isentropic


@pytest.mark.skip(reason="reference value not verified")
def test_stagnation_temperature_ratio_at_M1():
    # At M=1, T0/T has a known closed-form value (not a NACA table lookup),
    # but left skipped until the implementation and this check are confirmed.
    assert isentropic.stagnation_temperature_ratio(1.0) == pytest.approx(1.2)


@pytest.mark.skip(reason="reference value not verified")
def test_stagnation_pressure_ratio_table():
    # VERIFY: NACA 1135, Table I, M=2.0, gamma=1.4
    expected_p0_p = None  # TODO: fill in from NACA 1135 Table I
    assert isentropic.stagnation_pressure_ratio(2.0) == pytest.approx(expected_p0_p)


@pytest.mark.skip(reason="reference value not verified")
def test_stagnation_density_ratio_table():
    # VERIFY: NACA 1135, Table I, M=2.0, gamma=1.4
    expected_rho0_rho = None  # TODO: fill in from NACA 1135 Table I
    assert isentropic.stagnation_density_ratio(2.0) == pytest.approx(expected_rho0_rho)


@pytest.mark.skip(reason="reference value not verified")
def test_area_mach_ratio_at_M1():
    # A/A* = 1 at the sonic throat (M=1), a structural identity rather than
    # a table lookup, but left skipped until implementation is confirmed.
    assert isentropic.area_mach_ratio(1.0) == pytest.approx(1.0)


@pytest.mark.skip(reason="reference value not verified")
def test_area_mach_ratio_table():
    # VERIFY: NACA 1135, Table I, M=2.0, gamma=1.4
    expected_area_ratio = None  # TODO: fill in from NACA 1135 Table I
    assert isentropic.area_mach_ratio(2.0) == pytest.approx(expected_area_ratio)


@pytest.mark.skip(reason="reference value not verified")
def test_mach_from_area_ratio_supersonic_branch():
    # VERIFY: NACA 1135, Table I, A/A* -> M (supersonic branch)
    expected_M = None  # TODO: fill in from NACA 1135 Table I
    area_ratio = None  # TODO: corresponding A/A*
    assert isentropic.mach_from_area_ratio(area_ratio, supersonic=True) == pytest.approx(expected_M)


@pytest.mark.skip(reason="reference value not verified")
def test_mach_from_area_ratio_subsonic_branch():
    # VERIFY: NACA 1135, Table I, A/A* -> M (subsonic branch)
    expected_M = None  # TODO: fill in from NACA 1135 Table I
    area_ratio = None  # TODO: corresponding A/A*
    assert isentropic.mach_from_area_ratio(area_ratio, supersonic=False) == pytest.approx(expected_M)
