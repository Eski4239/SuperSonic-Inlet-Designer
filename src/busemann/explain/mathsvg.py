"""LaTeX (matplotlib mathtext subset) -> SVG bytes, cached. No Qt."""
import io
from functools import lru_cache

from matplotlib import mathtext
from matplotlib.font_manager import FontProperties

EQUATION_PT = 11.0      # font size of rendered equations, points (SVG units are pt)
PT_TO_PX = 4.0 / 3.0    # 1 pt = 1/72 in, 1 px = 1/96 in


@lru_cache(maxsize=512)
def tex_to_svg(tex, color="#111827", size_pt=EQUATION_PT):
    """SVG bytes of `$tex$`; raises ValueError if mathtext cannot parse it."""
    buf = io.BytesIO()
    mathtext.math_to_image(f"${tex}$", buf, prop=FontProperties(size=size_pt), format="svg",
                           color=color)
    return buf.getvalue()
