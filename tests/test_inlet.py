import pytest

from inletdesign import inlet
from inletdesign import normal_shock as ns


def test_no_ramps_matches_normal_shock_exactly():
    M_inf = 3.0
    states = inlet.compress(M_inf, [])
    assert len(states) == 1
    assert states[0].p0_ratio == ns.stagnation_pressure_ratio(M_inf)


def test_one_ramp_of_zero_degrees_same_as_no_ramps():
    M_inf = 3.0
    states_zero_ramp = inlet.compress(M_inf, [0.0])
    states_no_ramp = inlet.compress(M_inf, [])
    assert states_zero_ramp[-1].p0_ratio == pytest.approx(states_no_ramp[-1].p0_ratio, rel=1e-9)
    assert states_zero_ramp[-1].M == pytest.approx(states_no_ramp[-1].M, rel=1e-9)


@pytest.mark.parametrize(
    "M_inf, ramps", [(3.0, [8.0, 8.0]), (2.5, [10.0]), (4.0, [6.0, 6.0, 6.0])]
)
def test_total_temperature_conserved_and_p0_monotonic_decreasing(M_inf, ramps):
    states = inlet.compress(M_inf, ramps)
    prev_p0 = 1.0
    for state in states:
        assert state.T0_ratio == pytest.approx(1.0)
        assert state.p0_ratio <= prev_p0 + 1e-12
        prev_p0 = state.p0_ratio


def test_two_ramp_design_beats_normal_shock_at_M3():
    M_inf = 3.0
    states = inlet.compress(M_inf, [10.0, 10.0])
    recovery_with_ramps = states[-1].p0_ratio
    recovery_normal_shock_only = ns.stagnation_pressure_ratio(M_inf)
    assert recovery_with_ramps > recovery_normal_shock_only


def test_detached_ramp_raises_valueerror():
    with pytest.raises(ValueError):
        inlet.compress(2.0, [40.0])
