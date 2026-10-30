"""External cowl detachment check and the max-cowl-angle constrained optimum (M3.1)."""
import json

import numpy as np
import pytest

from inletdesign import api
from inletdesign import oblique_shock as obl
from inletdesign.geometry import COWL_MARGIN_WARN_DEG, cowl_check


def _cowl_notices(result):
    return [n for n in result.notices if n.text.startswith(("Cowl near", "External cowl"))]


# SOURCE: M3.1 review request (user-stated expectations: M3 2-ramp margin 0.28 +/- 0.01 deg,
# X-15 4-ramp detached, 1-ramp M2 no warning); the margin itself is the identity
# theta_max(M_inf) - sum(ramp angles).
def test_m3_two_ramp_is_near_detachment():
    d = api.design(3.0, 2)
    assert d.cowl_margin_deg == pytest.approx(0.28, abs=0.01)
    assert d.theta_max_freestream_deg == pytest.approx(obl.max_deflection(3.0)[0])
    assert d.cowl_margin_deg == pytest.approx(d.theta_max_freestream_deg - d.cowl_angle_deg)
    [notice] = _cowl_notices(d)
    assert notice.level == "warn"
    assert notice.text == f"Cowl near shock detachment (margin {d.cowl_margin_deg:.2f} deg)"


def test_x15_four_ramp_cowl_is_detached():
    d = api.design(6.7, 4)
    assert d.cowl_margin_deg < 0
    [notice] = _cowl_notices(d)
    assert notice.level == "error"
    assert notice.text.startswith("External cowl shock detached (cowl turns 59.50 deg")
    assert "bow shock, spillage and cowl drag not modelled" in notice.text


def test_one_ramp_m2_has_no_cowl_warning():
    d = api.design(2.0, 1)
    assert d.cowl_margin_deg > COWL_MARGIN_WARN_DEG
    assert not _cowl_notices(d)


def test_cowl_check_levels_are_closed_form():
    theta_max = obl.max_deflection(2.5)[0]
    assert cowl_check(2.5, theta_max - 3.0)[2] is None
    assert cowl_check(2.5, theta_max - 1.0)[2] == "warn"
    assert cowl_check(2.5, theta_max + 0.5)[2] == "error"


def test_off_design_applies_cowl_check_per_mach():
    d = api.design(3.0, 2)
    for M in (2.5, 3.0, 3.5):
        r = api.off_design_point(d, M)
        theta_max = obl.max_deflection(M)[0]
        assert r.cowl_margin_deg == pytest.approx(theta_max - d.cowl_angle_deg)
        level = cowl_check(M, d.cowl_angle_deg)[2]
        assert [n.level for n in _cowl_notices(r)] == ([level] if level else [])
    # below design Mach theta_max shrinks: the fixed cowl detaches
    low = api.off_design_point(d, 2.6)
    assert low.cowl_margin_deg < 0
    assert any(n.level == "error" for n in low.notices)
    json.dumps(low.to_dict())


# --- max cowl angle ------------------------------------------------------------------

def test_constrained_design_respects_limit():
    free = api.design(3.0, 2)
    d = api.design(3.0, 2, max_cowl_angle=30.0)
    assert d.constrained and not free.constrained
    assert d.cowl_angle_deg <= 30.0 + 1e-9
    assert d.cowl_angle_deg == pytest.approx(30.0, abs=1e-6)     # active limit binds
    assert d.recovery_total < free.recovery_total
    assert d.inputs.max_cowl_angle_deg == 30.0
    json.dumps(d.to_dict())


def test_recovery_falls_monotonically_as_limit_tightens():
    limits = np.linspace(33.0, 10.0, 24)
    recoveries = [api.design(3.0, 2, max_cowl_angle=float(L)).recovery_total for L in limits]
    assert all(b < a for a, b in zip(recoveries, recoveries[1:]))
    assert recoveries[0] <= api.design(3.0, 2).recovery_total


def test_inactive_limit_leaves_design_unchanged():
    free = api.design(3.0, 3)
    loose = api.design(3.0, 3, max_cowl_angle=80.0)
    assert not loose.constrained
    assert loose.ramp_angles_deg == free.ramp_angles_deg
    assert loose.recovery_total == free.recovery_total


def test_invalid_limit_and_custom_angles():
    with pytest.raises(ValueError, match="max cowl angle"):
        api.design(3.0, 2, max_cowl_angle=0.0)
    d = api.design(3.0, 2, ramp_angles=[10.0, 12.0], max_cowl_angle=15.0)
    assert not d.constrained
    assert any("ignored for custom angles" in w for w in d.warnings)
