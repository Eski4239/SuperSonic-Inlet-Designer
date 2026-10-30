"""Off-design chart data (pure Python): CFD overlay rule, series, regime bands."""
import math

import pytest

from busemann.charts import model
from inletdesign import api


def test_cfd_data_matches_phase3d_validation():
    data = model.load_cfd()
    # SOURCE: Phase 3d inviscid Fluent results, docs/validation_3d.md Results table rows
    # M 2.50-3.25 (capture CFD*, recovery CFD); values given by the user in the M4 request.
    assert [(p["M"], p["capture"], p["recovery"]) for p in data["points"]] == [
        (2.5, 0.770, 0.8466), (2.75, 0.888, 0.8283), (3.0, 1.000, 0.8011), (3.25, 1.004, 0.733)]
    assert "Mach reflection at lip; tool value is an upper bound" in data["points"][3]["note"]
    assert "M 3.5" in data["points"][3]["note"]
    assert all(p["M"] != 3.5 for p in data["points"])


@pytest.mark.parametrize("kwargs, applies", [
    (dict(M=3.0, n_ramps=2), True),
    (dict(M=3.0, n_ramps=2, cowl_wedge=6.0), True),
    (dict(M=3.0 + 1e-7, n_ramps=2), True),
    (dict(M=3.001, n_ramps=2), False),
    (dict(M=3.0, n_ramps=3), False),
    (dict(M=3.0, n_ramps=2, gamma=1.3), False),
    (dict(M=3.0, n_ramps=2, max_cowl_angle=30.0), False),
    (dict(M=3.0, n_ramps=2, ramp_angles=[15.0, 18.0]), False),
    (dict(M=6.7, n_ramps=4), False),
])
def test_cfd_applies_only_to_the_validated_design(kwargs, applies):
    M, n = kwargs.pop("M"), kwargs.pop("n_ramps")
    assert model.cfd_applies(api.design(M, n, **kwargs)) is applies
    assert model.cfd_applies(None) is False


def test_ordinal():
    assert [model.ordinal(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22)] == [
        "1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd"]


def test_margin_series_breaks_where_a_shock_crosses_the_lip():
    d = api.design(3.0, 2)
    sweep = api.off_design_sweep(d, 2.4, 3.6, 25)
    s = model.series(sweep)
    nan_at = [M for M, y in zip(s["margin_M"], s["margin"]) if math.isnan(y)]
    defined = [M for M, p in zip(sweep.machs, sweep.points) if p.cowl_margin_deg is not None]
    # one break at the region change (first point at/after design Mach), plus undefined points
    region_change = min(M for M, p in zip(sweep.machs, sweep.points) if p.cowl_lip_region == 0)
    assert region_change in nan_at
    assert set(nan_at) - {region_change} == {M for M in sweep.machs if M not in defined}
    assert len(s["M"]) == len(sweep.machs) == len(s["capture"])


def test_regime_bands_m3_two_ramp():
    d = api.design(3.0, 2)
    m_det = api.detachment_mach(d)
    sweep = api.off_design_sweep(d, m_det, 4.5, 40)
    bands = model.regime_bands(d, sweep, 1.2, 4.5)
    assert [(b.kind, b.label) for b in bands] == [
        ("detached", "2nd ramp shock detached"), ("spillage", "spillage"),
        ("overspeed", "overspeed: shocks inside cowl")]
    assert bands[0].lo == 1.2 and bands[0].hi == pytest.approx(m_det)
    assert bands[1].hi == bands[2].lo == 3.0 and bands[2].hi == 4.5


def test_cowl_detached_band_follows_local_rule_with_wedge():
    d = api.design(3.0, 2, cowl_wedge=6.0)
    sweep = api.off_design_sweep(d, api.detachment_mach(d), 4.5, 40)
    intervals = model.cowl_detached_intervals(d, sweep)
    assert len(intervals) == 2
    (a0, a1), (b0, b1) = intervals
    # lower: from where the lip flow turns supersonic to the attach Mach (STEP 0b: 2.66280)
    lip_supersonic = next(M / 1e4 for M in range(23862, 25000)
                          if api.off_design_point(d, M / 1e4).lip_mach >= 1.0)
    assert a0 == pytest.approx(lip_supersonic, abs=2e-4)
    assert a1 == pytest.approx(2.66280, abs=1e-4)
    # upper: from the design Mach (lip sees freestream) until theta_max(M) > cowl + wedge
    assert b0 == 3.0
    assert api.off_design_point(d, b1 - 1e-3).cowl_margin_deg < 0
    assert api.off_design_point(d, b1 + 1e-3).cowl_margin_deg > 0
    # without a wedge the 2-ramp design never detaches locally
    d0 = api.design(3.0, 2)
    assert model.cowl_detached_intervals(d0, api.off_design_sweep(d0, 2.39, 4.5, 40)) == []


def test_four_ramp_design_detached_from_design_mach_up():
    d = api.design(3.0, 4)
    sweep = api.off_design_sweep(d, api.detachment_mach(d), 4.5, 40)
    bands = model.regime_bands(d, sweep, 1.2, 4.5)
    assert bands[0].label == "4th ramp shock detached"
    assert [(b.lo, b.hi) for b in bands if b.kind == "cowl"] == [(3.0, 4.5)]
