import numpy as np
import pytest

from inletdesign import prandtl_meyer as pm


def test_nu_at_M1_is_zero():
    assert pm.nu(1.0) == pytest.approx(0.0, abs=1e-8)


@pytest.mark.parametrize("M", [1.2, 2.0, 3.0, 5.0, 8.0])
def test_mach_from_nu_round_trip(M):
    nu_val = pm.nu(M)
    assert pm.mach_from_nu(nu_val) == pytest.approx(M, rel=1e-6)


def test_accepts_arrays():
    M = np.array([1.0, 2.0, 3.0])
    assert pm.nu(M).shape == (3,)


# VERIFY against NACA 1135 (user-supplied, gamma=1.4; pending confirmation against the table)
def test_naca_1135_cross_check():
    assert pm.nu(2.0) == pytest.approx(26.38, rel=1e-3)
    assert pm.nu_max() == pytest.approx(130.45, rel=1e-3)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        pm.nu(0.5)
    with pytest.raises(ValueError):
        pm.nu(2.0, gamma=1.0)
    with pytest.raises(ValueError):
        pm.mach_from_nu(pm.nu_max())
