"""The continents."""

import math

from earth import state
from earth.config import COAST_STEP, LAND_EDGE, LAND_FILL, RADIUS
from earth.night import EDGE_DARK, LAND_DARK
from earth.data import CONTINENTS
from earth.window import line
from earth.geometry import CT, fill_split, ST


def densify(poly):
    """Adds intermediate points along the edges so the outline hugs the sphere, and converts to radians."""
    out = []
    n = len(poly)
    for i in range(n):
        lon1, lat1 = poly[i]
        lon2, lat2 = poly[(i + 1) % n]
        parts = max(1, math.ceil(max(abs(lon2 - lon1), abs(lat2 - lat1)) / COAST_STEP))
        for k in range(parts):
            t = k / parts
            out.append((
                math.radians(lat1 + (lat2 - lat1) * t),
                math.radians(lon1 + (lon2 - lon1) * t),
            ))
    return out


LAND = [densify(p) for p in CONTINENTS.values()]
# precomputed (cos lat, sin lat, sin lon, cos lon) for every vertex: rotating is then plain multiplication
LAND_T = [[(math.cos(la), math.sin(la), math.sin(lo), math.cos(lo)) for la, lo in poly] for poly in LAND]


def draw_land(rot):
    """Fill and outlines of the continents on the visible hemisphere."""
    cr, sr = math.cos(rot), math.sin(rot)
    for poly in LAND_T:
        pts = []
        front = False
        for cl, sl, slon, clon in poly:
            z0 = cl * (clon * cr - slon * sr)
            z = sl * ST + z0 * CT
            pts.append((cl * (slon * cr + clon * sr) * RADIUS, (sl * CT - z0 * ST) * RADIUS, z))
            if z >= 0:
                front = True
        if not front:
            continue  # continent is entirely on the far side

        # fill: far-side points are clamped to the edge of the disc
        flat = []
        for x, y, z in pts:
            if z < 0:
                d = math.hypot(x, y) or 1.0
                x, y = x / d * RADIUS, y / d * RADIUS
            flat.append((x, y))
        fill_split(flat, LAND_FILL, LAND_DARK)

        # outline: only where both points are on the near hemisphere; one polyline per continuous stretch
        # of the same side of the full-night line (day colour / night colour)
        n = len(pts)
        run, run_night = None, False
        for i in range(n):
            x1, y1, z1 = pts[i]
            x2, y2, z2 = pts[(i + 1) % n]
            if z1 >= 0 and z2 >= 0:
                night = (x1 + x2) < 2 * state.XE
                if run is not None and night != run_night:
                    line(run, EDGE_DARK if run_night else LAND_EDGE, 1.4)
                    run = [x1, -y1]
                if run is None:
                    run = [x1, -y1]
                run_night = night
                run += [x2, -y2]
            elif run is not None:
                line(run, EDGE_DARK if run_night else LAND_EDGE, 1.4)
                run = None
        if run is not None:
            line(run, EDGE_DARK if run_night else LAND_EDGE, 1.4)
