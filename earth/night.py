"""The day / night curve and the colours things have in full night."""

from earth.config import (
    CLOUD_BODY, CLOUD_HALO, CLOUD_SHADOW, LAND_EDGE, LAND_FILL, NIGHT_DARKNESS, NIGHT_END, NIGHT_START,
    NIGHT_STEPS, OCEAN, RADIUS,
)
from earth.state import layer_on
from earth.util import clamp01, lerp_color


N = NIGHT_STEPS


def darken(color):
    """The colour as it looks in full night (what the black night shade turns it into)."""
    return lerp_color(color, "#000000", NIGHT_DARKNESS)


LAND_DARK, EDGE_DARK = darken(LAND_FILL), darken(LAND_EDGE)
OCEAN_DARK = darken(OCEAN)
CLOUD_HALO_DARK, CLOUD_SHADOW_DARK, CLOUD_BODY_DARK = darken(CLOUD_HALO), darken(CLOUD_SHADOW), darken(CLOUD_BODY)


def night_factor(x):
    """0 = day ... 1 = full night for a screen x (pixels), smooth S-curve across the transition."""
    if not layer_on["night"]:
        return 0.0
    s = clamp01((NIGHT_START * RADIUS - x) / ((NIGHT_START - NIGHT_END) * RADIUS))
    return s * s * (3 - 2 * s)


XS = NIGHT_START * RADIUS  # right of this x it is full day


def night_level(x):
    """0 = day, N = full night (for x in pixels)."""
    if not layer_on["night"]:
        return 0
    f = (NIGHT_START * RADIUS - x) / ((NIGHT_START - NIGHT_END) * RADIUS)
    return max(0, min(N, round(f * N)))
