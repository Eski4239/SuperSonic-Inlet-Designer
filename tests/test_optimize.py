import numpy as np
import pytest

from inletdesign import normal_shock as ns
from inletdesign import oblique_shock as obl
from inletdesign import optimize as opt


@pytest.mark.parametrize("M_inf", [2.0, 3.0, 4.0])
@pytest.mark.parametrize("n_ramps", [1, 2, 3])
def test_numerical_and_equal_strength_agree(M_inf, n_ramps):
    eq = opt.optimize_equal_strength(M_inf, n_ramps)
    num = opt.optimize_numerical(M_inf, n_ramps)
    assert num["recovery"] == pytest.approx(eq["recovery"], rel=1e-4)


@pytest.mark.parametrize("M_inf", [2.0, 3.0, 4.0])
@pytest.mark.parametrize("n_ramps", [1, 2, 3])
def test_equal_strength_property(M_inf, n_ramps):
    result = opt.optimize_equal_strength(M_inf, n_ramps)
    M = M_inf
    for ramp_theta in result["ramps"]:
        beta = obl.beta_from_theta(M, ramp_theta)
        Mn = M * np.sin(np.radians(beta))
        assert Mn == pytest.approx(result["Mn"], rel=1e-8)
        state = obl.oblique_shock_state(M, ramp_theta)
        M = state["M2"]


@pytest.mark.parametrize("M_inf", [2.0, 3.0, 4.0])
@pytest.mark.parametrize("n_ramps", [1, 2, 3])
def test_terminal_mach_at_most_Mn(M_inf, n_ramps):
    result = opt.optimize_equal_strength(M_inf, n_ramps)
    terminal_state = result["states"][-1]
    assert terminal_state.M <= result["Mn"] + 1e-9


@pytest.mark.parametrize("M_inf", [2.0, 3.0, 4.0])
def test_recovery_increases_with_more_ramps(M_inf):
    recoveries = [opt.optimize_equal_strength(M_inf, n)["recovery"] for n in [0, 1, 2, 3]]
    assert recoveries == sorted(recoveries)
    assert len(set(recoveries)) == len(recoveries)


def test_zero_ramps_equals_normal_shock():
    for M_inf in [2.0, 3.0, 4.0]:
        result = opt.optimize_equal_strength(M_inf, 0)
        assert result["recovery"] == ns.stagnation_pressure_ratio(M_inf)
        assert result["ramps"] == []
        assert result["Mn"] is None


# REGRESSION: computed by this code (Phase 2b). Cross-check vs
# NACA TN 3589 Fig. 9 (n=1) and Fig. 11 (n=2).
@pytest.mark.parametrize("n_ramps, expected", [(1, 0.5812), (2, 0.7437), (3, 0.8361)])
def test_regression_recovery_at_M3(n_ramps, expected):
    result = opt.optimize_equal_strength(3.0, n_ramps)
    assert result["recovery"] == pytest.approx(expected, rel=1e-3)


def test_invalid_Mn_raises():
    with pytest.raises(ValueError):
        opt.equal_strength_ramps(3.0, 2, Mn=1.0)
    with pytest.raises(ValueError):
        opt.equal_strength_ramps(3.0, 2, Mn=3.0)
    with pytest.raises(ValueError):
        opt.equal_strength_ramps(3.0, 2, Mn=3.5)


def test_strong_branch_Mn_raises():
    # At M1=2.0, beta_at_theta_max ~ 64.67 deg; Mn = M1*sin(beta) ~ 1.96 forces
    # beta onto the strong branch (as found during debugging), which must be rejected.
    with pytest.raises(ValueError):
        opt.equal_strength_ramps(2.0, 1, Mn=1.9603513434014082)
