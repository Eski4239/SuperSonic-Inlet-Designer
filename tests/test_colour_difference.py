"""The CIEDE2000 test helper reproduces the published reference pairs."""
import pytest

from tests.colour_difference import ciede2000, delta_e


# SOURCE: Sharma, Wu & Dalal (2005), Color Res. Appl. 30(1), Table 1, pairs 1, 7 and 17
# (pending user confirmation, M4 STEP 1).
@pytest.mark.parametrize("lab1, lab2, expected", [
    ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
    ((50.0, 0.0, 0.0), (50.0, -1.0, 2.0), 2.3669),
    ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
])
def test_ciede2000_reference_pairs(lab1, lab2, expected):
    assert ciede2000(lab1, lab2) == pytest.approx(expected, abs=1e-4)


def test_identity_and_symmetry():
    assert delta_e("#123456", "#123456") == 0.0
    assert delta_e("#F7F0E5", "#E6D2B5") == pytest.approx(delta_e("#E6D2B5", "#F7F0E5"))
