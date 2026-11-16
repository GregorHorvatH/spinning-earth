"""Projection of the sphere onto the screen and polygon helpers."""

import math

from earth import state
from earth.config import RADIUS, TILT
from earth.window import tk_poly


CT, ST = math.cos(TILT), math.sin(TILT)


def project(lat, lon, rot):
    """Point on the sphere -> (x, y, z) after rotation about the axis and tilt."""
    x = math.cos(lat) * math.sin(lon + rot)
    y = math.sin(lat)
    z = math.cos(lat) * math.cos(lon + rot)
    # axial tilt (rotation about the X axis)
    y2 = y * math.cos(TILT) - z * math.sin(TILT)
    z2 = y * math.sin(TILT) + z * math.cos(TILT)
    return x * RADIUS, y2 * RADIUS, z2


def clip_left(poly, x_max):
    """Clips a 2D polygon with the half-plane x <= x_max."""
    out = []
    prev = poly[-1]
    for cur in poly:
        if (prev[0] <= x_max) != (cur[0] <= x_max):
            t = (x_max - prev[0]) / (cur[0] - prev[0])
            out.append((x_max, prev[1] + (cur[1] - prev[1]) * t))
        if cur[0] <= x_max:
            out.append(cur)
        prev = cur
    return out


def clip_right(poly, x_min):
    """Clips a 2D polygon with the half-plane x >= x_min (mirror of clip_left)."""
    return [(-x, y) for x, y in clip_left([(-x, y) for x, y in poly], -x_min)]


def fill_split(poly, day, night):
    """Fills a polygon with its day colour, or its night colour left of the full-night line XE
    (a polygon crossing XE is split in two). The gradient between day and night comes from the shade strip."""
    xs = [p[0] for p in poly]
    if min(xs) >= state.XE:
        fill(poly, day)
    elif max(xs) <= state.XE:
        fill(poly, night)
    else:
        fill(clip_left(poly, state.XE), night)
        fill(clip_right(poly, state.XE), day)


def fill(poly, color):
    if len(poly) >= 3:
        flat = []
        for x, y in poly:
            flat.append(x)
            flat.append(-y)
        tk_poly(flat, color)


def side_runs(points):
    """Splits a 3D polyline into runs on the near (z >= 0) and the far side of the globe:
    [(near, [x, y, x, y, ...]), ...] with canvas y already flipped."""
    runs = []
    for (x1, y1, z1), (x2, y2, z2) in zip(points, points[1:]):
        near = (z1 + z2) >= 0
        if runs and runs[-1][0] == near:
            runs[-1][1].extend((x2, -y2))
        else:
            runs.append((near, [x1, -y1, x2, -y2]))
    return runs
