import numpy as np
import pytest

from inletdesign import api, presets, units


@pytest.mark.parametrize("quantity", units.QUANTITIES)
@pytest.mark.parametrize("system", units.SYSTEMS)
def test_round_trip(quantity, system):
    values = np.array([0.0, 1.0, 123.456, 1e5])
    back = units.from_display(units.to_display(values, quantity, system), quantity, system)
    assert back == pytest.approx(values, rel=1e-12)


def test_scalar_returns_float():
    assert isinstance(units.to_display(1.0, "length", "Imperial"), float)


# Exact definitional identities (international foot/inch, avoirdupois pound, Rankine).
@pytest.mark.parametrize(
    "si, quantity, imperial",
    [
        (0.3048, "altitude", 1.0),
        (0.0254, "length", 1.0),
        (1.0, "temperature", 1.8),
        (0.45359237 / 0.3048, "mass_flow_per_span", 1.0),
        (0.3048, "velocity", 1.0),
    ],
)
def test_exact_definitions(si, quantity, imperial):
    assert units.to_display(si, quantity, "Imperial") == pytest.approx(imperial, rel=1e-12)


def test_psi_is_lbf_per_square_inch():
    assert units.PSI == pytest.approx(0.45359237 * 9.80665 / 0.0254**2, rel=1e-15)


def test_labels_and_errors():
    assert units.unit_label("pressure", "SI") == "kPa"
    assert units.unit_label("temperature", "Imperial") == "°R"
    with pytest.raises(ValueError):
        units.unit_label("pressure", "Metric")
    with pytest.raises(ValueError):
        units.to_display(1.0, "charm", "SI")


def test_presets_from_spec():
    names = [p.name for p in presets.PRESETS]
    assert names == ["Concorde cruise", "XB-70", "SR-71", "X-15 record", "Validation case"]
    for p in presets.PRESETS:
        assert p.description
        if p.mode == "altitude":
            fs = api.freestream(p.mach, altitude_m=p.altitude_m)
        else:
            fs = api.freestream(p.mach, p=p.p_pa, T=p.T_k)
        real_gas = any("real-gas" in w for w in fs.warnings)
        assert real_gas == (p.name == "X-15 record")


def test_validation_preset_is_manual():
    p = presets.get("Validation case")
    assert p.mode == "manual" and p.p_pa == 10000.0 and p.T_k == 220.0
    with pytest.raises(ValueError):
        presets.get("Blackbird")
