import pytest

from inletdesign import prandtl_meyer


@pytest.mark.skip(reason="reference value not verified")
def test_nu_at_M1_is_zero():
    # nu(1) = 0 by definition (zero turning angle to reach sonic condition).
    assert prandtl_meyer.nu(1.0) == pytest.approx(0.0)


@pytest.mark.skip(reason="reference value not verified")
def test_nu_table():
    # VERIFY: NACA 1135, Table III, M=2.0, gamma=1.4
    expected_nu = None  # TODO: fill in from NACA 1135 Table III
    assert prandtl_meyer.nu(2.0) == pytest.approx(expected_nu)


@pytest.mark.skip(reason="reference value not verified")
def test_mach_from_nu_table():
    # VERIFY: NACA 1135, Table III, nu -> M
    expected_M = None  # TODO: fill in from NACA 1135 Table III
    nu_value = None  # TODO: corresponding nu
    assert prandtl_meyer.mach_from_nu(nu_value) == pytest.approx(expected_M)


@pytest.mark.skip(reason="not yet implemented")
def test_nu_raises_for_subsonic_mach():
    with pytest.raises(ValueError):
        prandtl_meyer.nu(0.5)
