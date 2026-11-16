"""Orbits of the ordinary satellites and of the ISS."""

import math
import random

from earth.config import (
    ISS_BODY, ISS_BODY_NIGHT, ISS_INCLINATION, ISS_ORBIT, ISS_PANEL, ISS_PANEL_NIGHT, ISS_TRUSS,
    ISS_TRUSS_NIGHT, RADIUS, SAT_BODY, SAT_BODY_NIGHT, SAT_PANEL, SAT_PANEL_NIGHT, SAT_TRAIL_COLOR,
    SAT_TRAIL_NIGHT, SATELLITE_COUNT, SATELLITE_SEED, TILT,
)
from earth.util import cross, lerp_color, unit
from earth.night import N


def make_satellites():
    """Satellites on different orbits: (orbit radius in Earth radii, orbit-plane normal,
    speed [rad/frame; negative = opposite direction], initial phase)."""
    rnd = random.Random(SATELLITE_SEED)
    sats = []
    for _ in range(SATELLITE_COUNT):
        normal = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))
        speed = rnd.uniform(0.008, 0.022) * rnd.choice([1, 1, -1])
        sats.append((rnd.uniform(1.16, 1.32), normal, speed, rnd.uniform(0, 2 * math.pi)))
    return sats


SATELLITES = make_satellites()


def make_orbits():
    """Basis of each orbit plane: position = r·(cosθ·u + sinθ·v)."""
    orbits = []
    for factor, normal, omega, phase in SATELLITES:
        n = unit(normal)
        ref = (0.0, 1.0, 0.0) if abs(n[1]) < 0.9 else (1.0, 0.0, 0.0)
        u = unit(cross(n, ref))
        v = cross(n, u)
        orbits.append((factor * RADIUS, u, v, omega, phase))
    return orbits


ORBITS = make_orbits()
SAT_BODY_SHADES = [lerp_color(SAT_BODY, SAT_BODY_NIGHT, t / N) for t in range(N + 1)]
SAT_PANEL_SHADES = [lerp_color(SAT_PANEL, SAT_PANEL_NIGHT, t / N) for t in range(N + 1)]
SAT_TRAIL_SHADES = [lerp_color(SAT_TRAIL_COLOR, SAT_TRAIL_NIGHT, t / N) for t in range(N + 1)]


def make_iss():
    """ISS orbit: the plane is inclined by ISS_INCLINATION to Earth's rotation axis (taking its tilt into account)."""
    inc = math.radians(ISS_INCLINATION)
    n = (math.sin(inc), math.cos(inc) * math.cos(TILT), math.cos(inc) * math.sin(TILT))
    ref = (0.0, 1.0, 0.0) if abs(n[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = unit(cross(n, ref))
    v = cross(n, u)
    return ISS_ORBIT * RADIUS, u, v


ISS_R, ISS_U, ISS_V = make_iss()
ISS_BODY_SHADES = [lerp_color(ISS_BODY, ISS_BODY_NIGHT, t / N) for t in range(N + 1)]
ISS_TRUSS_SHADES = [lerp_color(ISS_TRUSS, ISS_TRUSS_NIGHT, t / N) for t in range(N + 1)]
ISS_PANEL_SHADES = [lerp_color(ISS_PANEL, ISS_PANEL_NIGHT, t / N) for t in range(N + 1)]
