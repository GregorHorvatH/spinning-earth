"""Clouds: a stream of cloud systems that is created behind the left horizon and destroyed past the right one."""

import math
import random

from earth import state
from earth.config import (
    CLOUD_BODY, CLOUD_DRIFT, CLOUD_HALO, CLOUD_SCALE, CLOUD_SHADOW, CLOUD_SYSTEMS, CLOUD_VERTS, RADIUS, SPEED,
)
from earth.night import CLOUD_BODY_DARK, CLOUD_HALO_DARK, CLOUD_SHADOW_DARK
from earth.window import tk_poly
from earth.geometry import clip_left, clip_right, CT, fill, ST


CLOUD_CS = [(math.cos(2 * math.pi * v / CLOUD_VERTS), math.sin(2 * math.pi * v / CLOUD_VERTS))
            for v in range(CLOUD_VERTS)]


CLOUD_RNG = random.Random(11)
CLOUD_GONE = math.radians(100)  # azimuth beyond which the whole system is already past the right horizon
cloud_counter = 0


def make_cloud_system(cloud_rot, center_az=None):
    """New cloud system (a cluster of fluffy puffs).

    center_az - azimuth of the centre relative to the viewer (rad). If omitted, the system is created
    entirely behind the left horizon (az < -95°) with a random delay before it appears in view.
    Clouds live in their own coordinate system: their longitude = azimuth - cloud_rot.
    """
    global cloud_counter
    rnd = CLOUD_RNG
    cloud_counter += 1
    clat = (1 if cloud_counter % 2 else -1) * rnd.uniform(4, 62)  # hemispheres alternate
    spread = rnd.uniform(5, 9)  # cluster extent along the parallel (degrees)
    puffs = []
    for _ in range(rnd.randint(8, 13)):
        dx = rnd.gauss(0, spread)
        dy = rnd.gauss(0, spread * 0.3)
        # puffs are larger at the cluster centre and smaller towards the edges
        r = max(1.8, rnd.uniform(2.2, 4.4) * (1.25 - min(1.0, abs(dx) / (2 * spread)) * 0.5))
        lat0 = max(-75, min(75, clat + dy))
        dlon = dx / max(0.35, math.cos(math.radians(clat)))
        puffs.append((lat0, dlon, r))

    if center_az is None:
        # the rightmost puff must be behind the left horizon, plus a random delay before it appears
        az_deg = -95 - rnd.uniform(0, 35) - max(p[1] for p in puffs)
    else:
        az_deg = math.degrees(center_az)
    center_lon = az_deg - math.degrees(cloud_rot)

    built = []
    lon_min = 1e9
    for lat0, dlon, r in puffs:
        lon_rad = math.radians(center_lon + dlon)
        phi = math.radians(lat0)
        cphi = math.cos(phi)
        k = max(0.35, cphi)
        # a puff is an ellipse in the tangent plane at its centre: semi-axes towards east / north (radians)
        a_east = math.radians(r * 1.15 * cphi / k)
        a_north = math.radians(r)
        built.append((cphi, math.sin(phi), math.sin(lon_rad), math.cos(lon_rad), a_east, a_north))
        lon_min = min(lon_min, lon_rad - a_east / k)
    return {"puffs": built, "min_lon": lon_min}


# initial set: systems scattered over the visible part and behind the left horizon
CLOUD_LIST = [
    make_cloud_system(0.0, math.radians(CLOUD_RNG.uniform(-130, 90)))
    for _ in range(CLOUD_SYSTEMS)
]


def update_clouds(cloud_rot):
    """Destroys systems that have fully passed the right horizon and creates new ones behind the left."""
    spawned = []
    for i, system in enumerate(CLOUD_LIST):
        if system["min_lon"] + cloud_rot > CLOUD_GONE:
            CLOUD_LIST[i] = make_cloud_system(cloud_rot)
            spawned.append(CLOUD_LIST[i])
    return spawned


def draw_clouds(rot):
    """Fluffy clouds: soft edge, shadow underneath, white top; they darken at night along with the surface.
    Each puff is projected once (its centre); its outline is then laid out with the local east/north
    directions, which also gives the foreshortening near the limb for free."""
    rot = state.tick * SPEED * CLOUD_DRIFT  # does not reset after a full revolution
    update_clouds(rot)
    if state.quality >= 3:
        return
    cr, sr = math.cos(rot), math.sin(rot)
    scale = RADIUS * CLOUD_SCALE
    puffs = []
    step = 2 if state.quality >= 2 else 1  # slow machine: a FIXED half of every cluster (its puffs never change)
    for system in CLOUD_LIST:
        for cphi, sphi, slon, clon, a_east, a_north in system["puffs"][::step]:
            sl = slon * cr + clon * sr          # sin(lon + rot)
            cl = clon * cr - slon * sr          # cos(lon + rot)
            if sphi * ST + cphi * cl * CT < 0.12:
                continue  # centre is too close to the edge or beyond the horizon
            # screen directions of "east" and "north" at the puff, scaled by the semi-axes
            ax, ay = a_east * cl * scale, a_east * sl * ST * scale
            bx, by = -a_north * sphi * sl * scale, a_north * (cphi * CT + sphi * cl * ST) * scale
            puffs.append((cphi * sl * scale, (sphi * CT - cphi * cl * ST) * scale, ax, ay, bx, by,
                          math.sqrt(ay * ay + by * by), math.sqrt(ax * ax + bx * bx)))

    # draw each layer for all puffs together so they merge into a single cloud
    cs = CLOUD_CS
    layers = ((1.3, 0.0, CLOUD_HALO, CLOUD_HALO_DARK),
              (1.0, -0.18, CLOUD_SHADOW, CLOUD_SHADOW_DARK),
              (0.88, 0.14, CLOUD_BODY, CLOUD_BODY_DARK))
    for f, shift, day, night in (layers[1:] if state.quality >= 1 else layers):
        for cx, cy, ax, ay, bx, by, hy, hx in puffs:
            fax, fbx, fay, fby = f * ax, f * bx, f * ay, f * by
            ym = -(cy + shift * hy)
            flat = [0.0] * (2 * CLOUD_VERTS)
            flat[0::2] = [cx + fax * c + fbx * s for c, s in cs]
            flat[1::2] = [ym - fay * c - fby * s for c, s in cs]
            if cx - f * hx >= state.XE:
                tk_poly(flat, day)
            elif cx + f * hx <= state.XE:
                tk_poly(flat, night)
            else:  # crosses the full-night line: split in two
                pts = [(flat[i], -flat[i + 1]) for i in range(0, len(flat), 2)]
                fill(clip_left(pts, state.XE), night)
                fill(clip_right(pts, state.XE), day)
