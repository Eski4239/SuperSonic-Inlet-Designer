import numpy as np
import pytest

from inletdesign import geometry as geo
from inletdesign import optimize as opt


def _point_to_line_distance(point, line_point, line_angle_deg):
    point = np.array(point, dtype=float)
    line_point = np.array(line_point, dtype=float)
    d = np.array([np.cos(np.radians(line_angle_deg)), np.sin(np.radians(line_angle_deg))])
    v = point - line_point
    proj = np.dot(v, d) * d
    perp = v - proj
    return np.linalg.norm(perp)


@pytest.mark.parametrize("M_inf, n_ramps", [(2.0, 1), (3.0, 2), (4.0, 3)])
def test_oblique_shocks_pass_through_lip(M_inf, n_ramps):
    design = opt.optimize_equal_strength(M_inf, n_ramps)
    g = geo.build_geometry(M_inf, design["ramps"])
    phis = [0.0]
    for theta in g.ramp_angles_deg:
        phis.append(phis[-1] + theta)

    for i in range(n_ramps):
        origin, _ = g.shocks[i]
        dist = _point_to_line_distance(g.lip, origin, phis[i] + g.betas_deg[i])
        assert dist < 1e-9 * g.capture_height


@pytest.mark.parametrize("M_inf, n_ramps", [(2.0, 1), (3.0, 2), (4.0, 3)])
def test_corners_on_ramp_and_shock_lines(M_inf, n_ramps):
    design = opt.optimize_equal_strength(M_inf, n_ramps)
    g = geo.build_geometry(M_inf, design["ramps"])
    phis = [0.0]
    for theta in g.ramp_angles_deg:
        phis.append(phis[-1] + theta)

    for i in range(1, n_ramps):
        corner = g.ramp_points[i]
        ramp_dist = _point_to_line_distance(corner, g.ramp_points[i - 1], phis[i])
        assert ramp_dist < 1e-9 * g.capture_height
        shock_dist = _point_to_line_distance(corner, g.lip, phis[i] + g.betas_deg[i])
        assert shock_dist < 1e-9 * g.capture_height


@pytest.mark.parametrize("M_inf, n_ramps", [(2.0, 1), (3.0, 2), (4.0, 3)])
def test_ramp_corners_strictly_increasing_and_slopes_match(M_inf, n_ramps):
    design = opt.optimize_equal_strength(M_inf, n_ramps)
    g = geo.build_geometry(M_inf, design["ramps"])
    xs = [p[0] for p in g.ramp_points]
    assert all(xs[i + 1] > xs[i] for i in range(len(xs) - 1))

    phis = [0.0]
    for theta in g.ramp_angles_deg:
        phis.append(phis[-1] + theta)
    for i in range(1, len(g.ramp_points)):
        p0, p1 = g.ramp_points[i - 1], g.ramp_points[i]
        slope = (p1[1] - p0[1]) / (p1[0] - p0[0])
        expected_slope = np.tan(np.radians(phis[i]))
        assert slope == pytest.approx(expected_slope, rel=1e-8)


@pytest.mark.parametrize("M_inf, n_ramps", [(2.0, 1), (3.0, 2), (4.0, 3)])
def test_mass_conservation(M_inf, n_ramps):
    design = opt.optimize_equal_strength(M_inf, n_ramps)
    g = geo.build_geometry(M_inf, design["ramps"])
    terminal = design["states"][-1]

    rhoV_inf = 1.0 * M_inf / np.sqrt(1.0)
    rhoV_after = terminal.p_ratio * terminal.M / np.sqrt(terminal.T_ratio)

    lhs = g.capture_height * rhoV_inf
    rhs = g.throat_height * rhoV_after
    assert lhs == pytest.approx(rhs, rel=1e-8)


def test_scaling():
    M_inf = 3.0
    ramps = [10.0, 12.0]
    g1 = geo.build_geometry(M_inf, ramps, capture_height=1.0, scale=1.0)
    g2 = geo.build_geometry(M_inf, ramps, capture_height=1.0, scale=2.0)

    for p1, p2 in zip(g1.ramp_points, g2.ramp_points):
        assert p2[0] == pytest.approx(2 * p1[0], abs=1e-9)
        assert p2[1] == pytest.approx(2 * p1[1], abs=1e-9)
    assert g2.lip[0] == pytest.approx(2 * g1.lip[0], abs=1e-9)
    assert g2.lip[1] == pytest.approx(2 * g1.lip[1], abs=1e-9)
    assert g2.capture_height == pytest.approx(2 * g1.capture_height)
    assert g2.throat_height == pytest.approx(2 * g1.throat_height)
    assert g2.ramp_angles_deg == g1.ramp_angles_deg
    assert g2.betas_deg == g1.betas_deg
    assert g2.cowl_angle_deg == g1.cowl_angle_deg


def test_zero_ramps():
    M_inf = 3.0
    g = geo.build_geometry(M_inf, [], capture_height=1.0)
    assert g.lip == (0.0, 1.0)
    assert len(g.shocks) == 1
    assert g.throat_height == pytest.approx(g.capture_height)


def test_infeasible_raises():
    with pytest.raises(ValueError):
        geo.build_geometry(2.0, [20.0, 20.0, 20.0])
