"""tooltips.json (no Qt): one sentence per key, every key used by the app, no unknown keys."""
import re
from pathlib import Path

import pytest

from busemann.tooltips import tip, tooltips

SRC = Path(__file__).resolve().parents[1] / "src" / "busemann"


def _sources():
    return "\n".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.py"))


def test_every_tooltip_is_one_sentence():
    for key, text in tooltips().items():
        assert text and text == text.strip(), key
        text = text.replace("U.S.", "US")            # abbreviation, not a sentence break
        assert text.endswith("."), key
        assert ". " not in text[:-1] and "? " not in text and "! " not in text, key


def test_every_key_is_used_and_every_used_key_exists():
    source = _sources()
    literal = set(re.findall(r"""["']([a-z_]+(?:\.[A-Za-z0-9_]+)+)["']""", source))
    prefixes = set(re.findall(r"""tip\(f["']([a-z_.]+)\{""", source))
    unused = [k for k in tooltips()
              if k not in literal and not any(k.startswith(p) for p in prefixes)]
    assert unused == []
    used = {k for k in literal if k.split(".")[0] in {key.split(".")[0] for key in tooltips()}}
    missing = sorted(k for k in used if k not in tooltips()
                     and not k.endswith((".md", ".json", ".svg", ".py")))
    assert missing == []


def test_unknown_key_raises():
    with pytest.raises(KeyError):
        tip("label.does_not_exist")
