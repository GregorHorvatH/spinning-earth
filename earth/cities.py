"""City lights on the night side."""

import math
import random

from earth import state
from earth.config import CITY_COLOR, CITY_DOTS, CITY_SPREAD, CITY_VISIBLE_FROM, LAND_NIGHT, RADIUS
from earth.util import lerp_color
from earth.night import N, night_level
from earth.data import CITIES, CONTINENTS
from earth.window import rect
from earth.geometry import CT, ST


def in_land(lat, lon):
    """Whether the point (degrees) falls inside any of our simplified land outlines."""
    for poly in CONTINENTS.values():
        inside = False
        j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        if inside:
            return True
    return False


def make_city_lights():
    """City lights: a bright core + a few smaller lights nearby; only where there is land on our map."""
    rnd = random.Random(21)
    dots = []
    for lat, lon in CITIES:
        candidates = [(lat, lon, 1.5, True)]
        for _ in range(CITY_DOTS):
            candidates.append((lat + rnd.gauss(0, CITY_SPREAD), lon + rnd.gauss(0, CITY_SPREAD),
                               rnd.uniform(0.6, 1.0), False))
        for la, lo, size, core in candidates:
            if in_land(la, lo):
                la, lo = math.radians(la), math.radians(lo)
                dots.append((math.cos(la), math.sin(la), math.sin(lo), math.cos(lo), size, core,
                             rnd.uniform(0, 2 * math.pi)))
    return dots


CITY_LIGHTS = make_city_lights()
CITY_LEVELS = 10
CITY_SHADES = [lerp_color(LAND_NIGHT, CITY_COLOR, i / CITY_LEVELS) for i in range(CITY_LEVELS + 1)]


def draw_cities(rot):
    """City lights: glow only on the night side, flicker slightly, hidden by clouds."""
    if state.quality >= 3:
        return
    cr, sr = math.cos(rot), math.sin(rot)
    for cl, sl, slon, clon, size, core, phase in CITY_LIGHTS:
        if state.quality >= 2 and not core:
            continue  # only the main light of each city
        z0 = cl * (clon * cr - slon * sr)
        z = sl * ST + z0 * CT
        if z < 0.08:
            continue  # beyond the horizon or too close to the edge
        x = cl * (slon * cr + clon * sr) * RADIUS
        y = (sl * CT - z0 * ST) * RADIUS
        depth = night_level(x) / N
        glow = (depth - CITY_VISIBLE_FROM) / (1 - CITY_VISIBLE_FROM)
        if glow <= 0:
            continue
        glow *= (0.85 + 0.15 * math.sin(state.tick * 0.03 + phase)) * (z ** 0.4)
        idx = int(min(1.0, glow) * CITY_LEVELS)
        if idx == 0:
            continue
        b = size * (0.6 + 0.4 * z)
        if core:  # soft glow around the city centre
            rect(x - b * 1.9, -y - b * 1.9, x + b * 1.9, -y + b * 1.9, CITY_SHADES[max(1, idx // 3)])
        rect(x - b, -y - b, x + b, -y + b, CITY_SHADES[idx])
