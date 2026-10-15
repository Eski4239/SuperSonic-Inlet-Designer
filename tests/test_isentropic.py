import numpy as np
import pytest

from inletdesign import isentropic as isen

# Reference values, gamma = 1.4. Cross-check one row against NACA 1135 Table I
# (the table lists p/p0, T/T0, rho/rho0 - the inverses of these).
REFERENCE = [
    # M,   T0/T,  p0/p,   rho0/rho, A/A*
    (1.0,  1.2,   1.8929, 1.5774,   1.0),
    (2.0,  1.8,   7.8245, 4.3469,   1.6875),
]


@pytest.mark.parametrize("M, T, p, rho, A", REFERENCE)
def test_forward_relations(M, T, p, rho, A):
    assert isen.stagnation_temperature_ratio(M) == pytest.approx(T, rel=1e-4)
    assert isen.stagnation_pressure_ratio(M) == pytest.approx(p, rel=1e-4)
    assert isen.stagnation_density_ratio(M) == pytest.approx(rho, rel=1e-4)
    assert isen.area_mach_ratio(M) == pytest.approx(A, rel=1e-4)


def test_stagnation_ratios_at_rest_are_one():
    assert isen.stagnation_temperature_ratio(0.0) == pytest.approx(1.0)
    assert isen.stagnation_pressure_ratio(0.0) == pytest.approx(1.0)


def test_accepts_arrays():
    M = np.array([0.5, 1.0, 2.0])
    assert isen.stagnation_temperature_ratio(M).shape == (3,)


@pytest.mark.parametrize("M", [0.2, 0.5, 0.9, 1.5, 2.0, 3.0, 5.0, 8.0])
def test_area_ratio_round_trip(M):
    ratio = isen.area_mach_ratio(M)
    recovered = isen.mach_from_area_ratio(ratio, supersonic=(M > 1))
    assert recovered == pytest.approx(M, rel=1e-8)


def test_area_ratio_one_is_sonic():
    assert isen.mach_from_area_ratio(1.0) == 1.0


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        isen.stagnation_temperature_ratio(-1.0)
    with pytest.raises(ValueError):
        isen.area_mach_ratio(0.0)
    with pytest.raises(ValueError):
        isen.mach_from_area_ratio(0.5)