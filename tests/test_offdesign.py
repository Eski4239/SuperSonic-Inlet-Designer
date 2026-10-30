import numpy as np
import pytest

from inletdesign import inlet as _inlet
from inletdesign.cli import main
from inletdesign.geometry import design_inlet
from inletdesign.offdesign import off_design
from inletdesign.optimize import optimize_equal_strength


@pytest.fixture
def geom():
    return design_inlet(3.0, 2, capture_height=1.0)


def test_on_lip_at_design_mach(geom):
    result = off_design(geom, 3.0)
    assert result.regime == "on-lip"
    assert result.mass_capture_ratio == pytest.approx(1.0, abs=1e-9)
    assert result.recovery_total == pytest.approx(0.7437, rel=1e-3)
    live_recovery = optimize_equal_strength(3.0, 2)["recovery"]
    assert result.recovery_total == pytest.approx(live_recovery, abs=1e-6)


def test_spillage_below_design(geom):
    r1 = off_design(geom, 2.5)
    r2 = off_design(geom, 2.75)
    assert r1.regime == "spillage"
    assert r2.regime == "spillage"
    assert 0 < r1.mass_capture_ratio < 1
    assert 0 < r2.mass_capture_ratio < 1
    assert r1.mass_capture_ratio < r2.mass_capture_ratio


def test_shock_in_duct_above_design(geom):
    for M in (3.25, 3.5):
        result = off_design(geom, M)
        assert result.regime == "shock-in-duct"
        assert result.mass_capture_ratio == pytest.approx(1.0, abs=1e-9)
        assert (
            "internal reflected shock not modelled; recovery is an upper bound"
            in result.warnings
        )


def test_mass_capture_ratio_never_exceeds_one(geom):
    for M in (2.3, 2.5, 2.75, 3.0, 3.25, 3.5, 4.0):
        try:
            result = off_design(geom, M)
        except ValueError:
            continue
        assert result.mass_capture_ratio <= 1.0 + 1e-9


def test_detached_raises(geom):
    with pytest.raises(ValueError):
        off_design(geom, 2.0)


def _ramp_y_at(ramp_points, x):
    for i in range(len(ramp_points) - 1):
        x0, y0 = ramp_points[i]
        x1, y1 = ramp_points[i + 1]
        if x0 <= x <= x1 or i == len(ramp_points) - 2:
            frac = (x - x0) / (x1 - x0) if x1 != x0 else 0.0
            return y0 + frac * (y1 - y0)
    return ramp_points[-1][1]


@pytest.mark.parametrize("M_inf", [2.5, 2.75, 3.0])
def test_mass_conservation_vertical_cut(geom, M_inf):
    from inletdesign import oblique_shock as obl

    h_c = geom.capture_height
    ramp_angles = geom.ramp_angles_deg
    ramp_points = geom.ramp_points
    lip = geom.lip
    n = len(ramp_angles)

    phis = [0.0]
    M = M_inf
    betas = []
    for theta in ramp_angles:
        state = obl.oblique_shock_state(M, theta, weak=True)
        betas.append(state["beta"])
        M = state["M2"]
        phis.append(phis[-1] + theta)

    states = _inlet.compress(M_inf, ramp_angles)
    x_lip = lip[0]
    y_bottom = _ramp_y_at(ramp_points, x_lip)
    y_top = h_c

    shock_crossings_y = []
    for i in range(n):
        origin = np.array(ramp_points[i])
        angle = np.radians(phis[i] + betas[i])
        d = np.array([np.cos(angle), np.sin(angle)])
        if abs(d[0]) < 1e-12:
            continue
        t = (x_lip - origin[0]) / d[0]
        y_at_cut = origin[1] + t * d[1]
        shock_crossings_y.append((i, y_at_cut, t))

    valid = [
        (i, y) for i, y, t in shock_crossings_y
        if y_bottom - 1e-9 <= y <= y_top + 1e-9 and t > -1e-9
    ]
    valid.sort(key=lambda p: p[1])

    boundaries = [y_bottom] + [y for i, y in valid] + [y_top]
    region_mach = [M_inf] + [s.M for s in states[:-1]]
    region_p_ratio = [1.0] + [s.p_ratio for s in states[:-1]]
    region_T_ratio = [1.0] + [s.T_ratio for s in states[:-1]]

    remaining = n
    region_sequence = []
    for _ in valid:
        region_sequence.append(remaining)
        remaining -= 1
    region_sequence.append(remaining)

    mdot_cut = 0.0
    for seg in range(len(boundaries) - 1):
        y0, y1 = boundaries[seg], boundaries[seg + 1]
        dy = y1 - y0
        region = region_sequence[seg]
        M_r, p_r, T_r = region_mach[region], region_p_ratio[region], region_T_ratio[region]
        phi_r = np.radians(phis[region])
        rhoV = p_r * M_r / np.sqrt(T_r)
        mdot_cut += rhoV * np.cos(phi_r) * dy

    result = off_design(geom, M_inf)
    expected = 1.0 * M_inf * result.mass_capture_ratio * h_c
    assert mdot_cut == pytest.approx(expected, rel=1e-9)


def test_cli_offdesign_smoke(capsys):
    code = main(
        [
            "offdesign", "--design-mach", "3", "--ramps", "2",
            "--mach", "2.5", "2.75", "3", "3.25", "3.5",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "spillage" in captured.out
    assert "shock-in-duct" in captured.out


def test_cli_offdesign_json_and_plot(tmp_path):
    json_path = tmp_path / "offdesign.json"
    plot_path = tmp_path / "offdesign.png"
    code = main(
        [
            "offdesign", "--design-mach", "3", "--ramps", "2",
            "--mach", "2.5", "2.75", "3", "3.25", "3.5",
            "--json", str(json_path), "--plot", str(plot_path),
        ]
    )
    assert code == 0
    assert json_path.exists()
    assert plot_path.exists()


def test_sweep_near_detachment_never_raises_unexpectedly():
    """Spec section 6: M 2.39 -> 3.5 in 0.005 steps, result or documented detachment error."""
    from inletdesign.offdesign import SUBSONIC_WARNING

    geom = design_inlet(3.0, 2, capture_height=0.1)
    n_subsonic = 0
    for M in np.round(np.arange(2.39, 3.5 + 1e-9, 0.005), 3):
        try:
            r = off_design(geom, float(M))
        except ValueError as exc:
            assert "shock detached" in str(exc)
            continue
        if r.M_duct < 1.0:
            n_subsonic += 1
            assert SUBSONIC_WARNING in r.warnings
            assert r.recovery_total == r.recovery_oblique
        else:
            assert SUBSONIC_WARNING not in r.warnings
            assert r.recovery_total < r.recovery_oblique
    assert n_subsonic > 0  # the band exists for this design


def test_zero_ramp_geometry_has_no_off_design_model():
    from inletdesign import api

    d = api.design(3.0, 0)
    with pytest.raises(ValueError, match="needs at least one ramp"):
        api.off_design_point(d, 3.0)
    with pytest.raises(ValueError, match="needs at least one ramp"):
        api.off_design_sweep(d, 2.0, 4.0, 5)
