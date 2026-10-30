"""Performance targets (spec 7, M3) and a regression lock on the validated numbers."""
import statistics
import time

import pytest

from inletdesign import api

pytestmark = pytest.mark.perf


def _median_ms(fn, runs=20):
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times)


def test_design_under_50_ms():
    uncached = api._design_cached.__wrapped__   # time the computation, not the LRU cache
    assert _median_ms(lambda: uncached(3.0, 2, 0.1, 1.4, None)) < 50.0


def test_off_design_curve_40_points_under_150_ms():
    d = api.design(3.0, 2)
    assert _median_ms(lambda: api.off_design_sweep(d, 2.0, 3.5, 40)) < 150.0


def test_sweep_100_points_under_500_ms():
    d = api.design(3.0, 2)
    assert _median_ms(lambda: api.off_design_sweep(d, 2.0, 3.5, 100), runs=5) < 500.0


# SOURCE: docs/validation_3b.md (M3 design recovery) and docs/validation_3d.md table
# (tool recovery_oblique at M 2.50 / 2.75 / 3.00); values restated and confirmed by the user
# in the M3 request, to stay within 1e-4 after the solver speed-up.
def test_validated_numbers_unchanged():
    d = api.design(3.0, 2, capture_height=0.1)
    assert d.recovery_total == pytest.approx(0.7437, abs=1e-4)
    for M, expected in ((2.5, 0.8473), (2.75, 0.8288), (3.0, 0.8018)):
        assert api.off_design_point(d, M).recovery_oblique == pytest.approx(expected, abs=1e-4)


def _app_sweep(d):
    """What the app's design job adds per design change: detachment Mach + 40-point sweep
    over the off-design slider range."""
    m_det = api.detachment_mach(d)
    return api.off_design_sweep(d, max(1.2, m_det), d.inputs.M + 1.5, 40)


@pytest.mark.parametrize("M, n, wedge", [(3.0, 2, 0.0), (3.0, 4, 0.0), (6.7, 4, 0.0),
                                         (3.0, 2, 6.0)])
def test_app_off_design_sweep_under_150_ms(M, n, wedge):
    d = api.design(M, n, cowl_wedge=wedge)
    assert _median_ms(lambda: _app_sweep(d), runs=10) < 150.0


def test_regime_bands_with_wedge_under_50_ms():
    from busemann.charts import model

    d = api.design(3.0, 2, cowl_wedge=6.0)
    sweep = _app_sweep(d)
    assert _median_ms(lambda: model.regime_bands(d, sweep, 1.2, 4.5), runs=10) < 50.0


def test_slider_off_design_point_under_5_ms():
    """The light job run per slider step while dragging."""
    d = api.design(3.0, 4)
    assert _median_ms(lambda: api.off_design_point(d, 3.137), runs=50) < 5.0
