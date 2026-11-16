"""Pre-rendered RGBA images (as PNG, built in pure Python): the atmosphere glow and the night gradient."""

import math

from earth import state
from earth.config import ATMO_COLOR, ATMO_NIGHT, ATMO_STRENGTH, ATMO_WIDTH, NIGHT_DARKNESS, NIGHT_END, RADIUS
from earth.util import clamp01, png_rgba, rgb
from earth.night import night_factor, XS


ATMO_TILES = 32  # the atmosphere ring is split into this many small images (tiny pixel area for Tk to blend)


def make_atmo_tiles(k):
    """Atmosphere glow as a ring of small RGBA images (day side bright, night side dimmed).
    Returns [(screen_x, screen_y, png), ...]. Small tiles keep the blended pixel area low."""
    r_out = RADIUS + ATMO_WIDTH
    r_in = RADIUS - 1.5 / k
    inv = 1.0 / k
    ar, ag, ab = rgb(ATMO_COLOR)
    two_pi = 2 * math.pi
    atan2, hypot, floor, ceil = math.atan2, math.hypot, math.floor, math.ceil
    tiles = []
    for t in range(ATMO_TILES):
        a0, a1 = two_pi * t / ATMO_TILES, two_pi * (t + 1) / ATMO_TILES
        corners = [(r * math.cos(a), r * math.sin(a)) for r in (r_in, r_out) for a in (a0, a1)]
        for q in range(4):                                   # axis extremes that fall inside the sector
            a = q * math.pi / 2
            if a0 < a < a1:
                corners.append((r_out * math.cos(a), r_out * math.sin(a)))
        if max(c[0] for c in corners) <= state.XE:
            continue  # deep in the night the glow is almost invisible - skip the whole tile
        x0 = floor(min(c[0] for c in corners) * k) - 1
        x1 = ceil(max(c[0] for c in corners) * k) + 1
        y0 = floor(min(c[1] for c in corners) * k) - 1
        y1 = ceil(max(c[1] for c in corners) * k) + 1
        zero4 = bytes(4)
        rows = []
        for py in range(y1 - y0):
            sy = y0 + py + 0.5
            row = []
            for px in range(x1 - x0):
                sx = x0 + px + 0.5
                r = hypot(sx, sy) * inv
                if r < r_in or r > r_out:
                    row.append(zero4)
                    continue
                theta = atan2(sy, sx) % two_pi
                if not (a0 <= theta < a1):
                    row.append(zero4)
                    continue
                tt = (r_out - r) / ATMO_WIDTH
                glow = 1 - (1 - ATMO_NIGHT) * night_factor(sx * inv)
                row.append(bytes((ar, ag, ab, int(ATMO_STRENGTH * tt * tt * glow * 255 + 0.5))))
            rows.append(b"".join(row))
        tiles.append((x0, y0, png_rgba(x1 - x0, y1 - y0, rows)))
    return tiles


def make_night_strip(k):
    """The gradient only: a black image whose alpha ramps up across the day/night transition, masked to the
    globe disc. Deep night is drawn with plain dark colours, so this image stays narrow."""
    r_o = RADIUS + 0.8  # just the globe disc (a wider mask would darken a sliver of sky outside the limb)
    inv = 1.0 / k
    x0 = int(math.ceil(NIGHT_END * RADIUS * k))  # the strip starts on a pixel boundary, right of the old XE
    width = int(math.ceil(XS * k)) - x0 + 1
    top = int(math.ceil(r_o * k)) + 1
    height = 2 * top
    alpha = [int(255 * NIGHT_DARKNESS * night_factor((x0 + px + 0.5) * inv) + 0.5) for px in range(width)]
    col4 = [bytes((0, 0, 0, a)) for a in alpha]
    zero4 = bytes(4)
    sqrt = math.sqrt

    def edge(px, dy2):
        dx = (x0 + px + 0.5) * inv
        c = clamp01((r_o - sqrt(dx * dx + dy2)) * k + 0.5)   # anti-aliased limb
        return bytes((0, 0, 0, int(alpha[px] * c + 0.5)))

    rows = []
    for py in range(height):
        dy = (py + 0.5 - top) * inv
        dy2 = dy * dy
        wo2 = (r_o + inv) ** 2 - dy2
        if wo2 <= 0:
            rows.append(zero4 * width)
            continue
        wo = sqrt(wo2)
        b1 = max(0, int(math.ceil(-wo * k - 0.5)) - x0)
        b2 = min(width, int(math.floor(wo * k - 0.5)) - x0 + 1)
        wi2 = (r_o - 1.5 * inv) ** 2 - dy2
        if wi2 > 0:
            wi = sqrt(wi2)
            a1 = min(max(b1, int(math.ceil(-wi * k - 0.5)) - x0), b2)
            a2 = max(a1, min(b2, int(math.floor(wi * k - 0.5)) - x0 + 1))
        else:
            a1 = a2 = (b1 + b2) // 2
        parts = [zero4 * b1]
        parts += [edge(px, dy2) for px in range(b1, a1)]
        parts.append(b"".join(col4[a1:a2]))
        parts += [edge(px, dy2) for px in range(a2, b2)]
        parts.append(zero4 * (width - b2))
        rows.append(b"".join(parts))
    return x0, top, width, height, png_rgba(width, height, rows)
