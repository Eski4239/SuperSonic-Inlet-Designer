import numpy as np
import pytest

from inletdesign import normal_shock as ns


@pytest.mark.parametrize("M1", [1.0])
def test_at_M1_equals_1_nothing_changes(M1):
    assert ns.mach_downstream(M1) == pytest.approx(1.0)
    assert ns.pressure_ratio(M1) == pytest.approx(1.0)
    assert ns.temperature_ratio(M1) == pytest.approx(1.0)
    assert ns.density_ratio(M1) == pytest.approx(1.0)
    assert ns.stagnation_pressure_ratio(M1) == pytest.approx(1.0)


@pytest.mark.parametrize("M1", [1.5, 2.0, 3.0, 5.0])
def test_stagnation_pressure_ratio_less_than_one(M1):
    assert ns.stagnation_pressure_ratio(M1) < 1.0


@pytest.mark.parametrize("M1", [1.5, 2.0, 3.0, 5.0])
def test_downstream_mach_is_subsonic(M1):
    assert ns.mach_downstream(M1) < 1.0


# SOURCE: NACA 1135 normal-shock table, M1=2.00 (tabulated to 4 s.f.: M2 0.5774, p2/p1 4.500,
# T2/T1 1.688, rho2/rho1 2.667, p02/p01 0.7209). Test values are the exact closed-form results.
def test_naca_1135_cross_check_M1_2():
    assert ns.mach_downstream(2.0) == pytest.approx(0.5774, rel=1e-3)
    assert ns.pressure_ratio(2.0) == pytest.approx(4.5, rel=1e-3)
    assert ns.temperature_ratio(2.0) == pytest.approx(1.6875, rel=1e-3)
    assert ns.density_ratio(2.0) == pytest.approx(2.6667, rel=1e-3)
    assert ns.stagnation_pressure_ratio(2.0) == pytest.approx(0.7209, rel=1e-3)


def test_accepts_arrays():
    M1 = np.array([1.0, 2.0, 3.0])
    assert ns.mach_downstream(M1).shape == (3,)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        ns.mach_downstream(0.5)
    with pytest.raises(ValueError):
        ns.pressure_ratio(2.0, gamma=1.0)
