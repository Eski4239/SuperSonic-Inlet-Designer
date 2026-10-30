import numpy as np
import pytest

from inletdesign import atmosphere as atm

# Layer-base values of the 1976 standard, at GEOPOTENTIAL altitude H.
# SOURCE: U.S. Standard Atmosphere 1976 (NOAA-S/T 76-1562), Table 4 (defining
# layer-base T_b, P_b) and Table I (density) -- page numbers TO CONFIRM.
# UNCONFIRMED: entered from memory, awaiting user check against the document.
LAYER_BASES = [
    # H (m),  T (K),  p (Pa),     rho (kg/m^3)
    (0.0,     288.15, 101325.0,   1.2250),
    (11000.0, 216.65, 22632.06,   0.36392),
    (20000.0, 216.65, 5474.889,   0.088035),
    (32000.0, 228.65, 868.0187,   0.013225),
    (47000.0, 270.65, 110.9063,   0.0014275),
]

# Spot values at GEOMETRIC altitude z.
# SOURCE: U.S. Standard Atmosphere 1976 (NOAA-S/T 76-1562), Table I -- page TO CONFIRM.
# UNCONFIRMED: entered from memory, awaiting user check against the document.
GEOMETRIC = [
    # z (m),  T (K),   p (Pa),   rho (kg/m^3)
    (11000.0, 216.774, 22699.9,  0.36480),
    (20000.0, 216.650, 5529.3,   0.088910),
    # 32 km row removed: my recalled T = 228.756 K contradicts the layer definition
    # (H = 31.84 km lies in the 1 K/km layer -> 228.49 K). Re-add from the document.
]


@pytest.mark.parametrize("H, T, p, rho", LAYER_BASES)
def test_layer_base_values(H, T, p, rho):
    z = atm.geometric_altitude(H)
    assert atm.temperature(z) == pytest.approx(T, rel=1e-3)
    assert atm.pressure(z) == pytest.approx(p, rel=1e-3)
    assert atm.density(z) == pytest.approx(rho, rel=1e-3)


@pytest.mark.parametrize("z, T, p, rho", GEOMETRIC)
def test_geometric_table_values(z, T, p, rho):
    assert atm.temperature(z) == pytest.approx(T, rel=1e-3)
    assert atm.pressure(z) == pytest.approx(p, rel=1e-3)
    assert atm.density(z) == pytest.approx(rho, rel=1e-3)


def test_geopotential_round_trip():
    z = np.linspace(0.0, 86000.0, 50)
    assert atm.geometric_altitude(atm.geopotential_altitude(z)) == pytest.approx(z, abs=1e-6)


@pytest.mark.parametrize("H_base", [11000.0, 20000.0, 32000.0, 47000.0, 51000.0, 71000.0])
def test_continuous_across_layer_bases(H_base):
    z = atm.geometric_altitude(H_base)
    below, above = z - 1e-3, z + 1e-3
    assert atm.temperature(below) == pytest.approx(atm.temperature(above), rel=1e-6)
    assert atm.pressure(below) == pytest.approx(atm.pressure(above), rel=1e-6)


def test_pressure_monotonic_decreasing():
    p = atm.pressure(np.linspace(0.0, 86000.0, 400))
    assert np.all(np.diff(p) < 0)


def test_ideal_gas_and_speed_of_sound_identities():
    z = np.array([0.0, 15000.0, 60000.0])
    T = atm.temperature(z)
    assert atm.density(z) == pytest.approx(atm.pressure(z) / (atm.R_AIR * T))
    assert atm.speed_of_sound(z) == pytest.approx(np.sqrt(1.4 * atm.R_AIR * T))


def test_accepts_arrays():
    z = np.array([0.0, 10000.0, 80000.0])
    for f in (atm.temperature, atm.pressure, atm.density, atm.speed_of_sound):
        assert f(z).shape == (3,)


@pytest.mark.parametrize("z", [-1.0, 86001.0, float("nan")])
def test_out_of_range_raises(z):
    with pytest.raises(ValueError):
        atm.temperature(z)


def test_sutherland_reference_point_is_closed_form():
    T = 288.15
    expected = atm.SUTHERLAND_BETA * T**1.5 / (T + atm.SUTHERLAND_S)
    assert atm.dynamic_viscosity(T) == pytest.approx(expected)
    with pytest.raises(ValueError):
        atm.dynamic_viscosity(0.0)
