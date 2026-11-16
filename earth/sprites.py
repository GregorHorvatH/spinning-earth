"""Drawing of the objects of the game: satellites, the ISS, the turtle, a burning wreck, the target ring and flashes."""

import math

from earth import state
from earth.config import (
    BG, CATCH_RADIUS, HUD_CLOSE, ISS_BODY, ISS_LABEL, ISS_PANEL, ISS_SIZE, ISS_TRAIL, ISS_TRAIL_COLOR,
    ISS_TRUSS, PLAYER_COLOR, PLAYER_COLOR_NIGHT, PLAYER_EDGE, PLAYER_EDGE_NIGHT, PLAYER_PATH, PLAYER_SIZE,
    PLAYER_TRAIL, PLAYER_TRAIL_NIGHT, RADIUS, SAT_TRAIL, SAT_TRAIL_STEP, TRAIL_GROUPS,
)
from earth.state import layer_on
from earth.util import clamp01, dist, lerp_color
from earth.night import night_factor, night_level
from earth.window import cv, line
from earth.geometry import side_runs
from earth.orbits import (
    ISS_BODY_SHADES, ISS_PANEL_SHADES, ISS_TRUSS_SHADES, ORBITS, SAT_BODY_SHADES, SAT_PANEL_SHADES,
    SAT_TRAIL_SHADES,
)
from earth.game import (
    active_satellites, BURN_COLORS, EFFECT_LIFE, effects, fire_color, iss, iss_pos, player, player_pos,
    WOBBLE_LIFE, wreck_state, wrecks,
)


def draw_satellites(front):
    """Satellites with trails. front=False - those behind the Earth (drawn before the globe, so the globe covers them)."""
    for r, u, v, omega, phase in ORBITS[:active_satellites()]:
        direction = 1 if omega > 0 else -1
        theta = phase + omega * state.tick
        pts = []
        for j in range(SAT_TRAIL + 1):
            t = theta - direction * j * SAT_TRAIL_STEP
            c, sn = math.cos(t), math.sin(t)
            pts.append((r * (c * u[0] + sn * v[0]),
                        r * (c * u[1] + sn * v[1]),
                        r * (c * u[2] + sn * v[2])))

        # trail: a few polylines that fade out to the background colour (not one item per step)
        group, run = -1, None
        for j in range(0 if state.quality >= 2 else SAT_TRAIL):
            (x1, y1, z1), (x2, y2, z2) = pts[j], pts[j + 1]
            if ((z1 + z2) >= 0) != front:
                if run:
                    line(run, run_color, 2)
                run, group = None, -1
                continue
            g = j * TRAIL_GROUPS // SAT_TRAIL
            if run is None or g != group:
                if run:
                    line(run, run_color, 2)
                run, group = [x1, -y1], g
                run_color = lerp_color(BG, SAT_TRAIL_SHADES[night_level((x1 + x2) / 2)], 1 - (g + 0.5) / TRAIL_GROUPS)
            run += [x2, -y2]
        if run:
            line(run, run_color, 2)

        # body with two solar panels
        x, y, z = pts[0]
        if (z >= 0) != front:
            continue
        lvl = night_level(x)
        k = 0.85 + 0.15 * z / r  # closer to the viewer = slightly larger
        cv.create_line(x - 11 * k, -y, x + 11 * k, -y, fill=SAT_PANEL_SHADES[lvl], width=3)
        b = 2.8 * k
        cv.create_rectangle(x - b, -y - b, x + b, -y + b, fill=SAT_BODY_SHADES[lvl], outline="")


def draw_iss(front):
    """ISS: truss, four pairs of golden solar arrays, white modules, trail and label.
    front=False - when the station is behind the Earth (drawn before the globe, so the globe covers it)."""
    theta, iss_r, iss_u, iss_v = iss["theta"], iss["r"], iss["u"], iss["v"]
    pts = []
    trail_step = min(SAT_TRAIL_STEP, iss["omega"] * 6)  # a station that hardly moves has hardly any trail
    for j in range(ISS_TRAIL + 1):
        t = theta - j * trail_step
        c, sn = math.cos(t), math.sin(t)
        pts.append((iss_r * (c * iss_u[0] + sn * iss_v[0]),
                    iss_r * (c * iss_u[1] + sn * iss_v[1]),
                    iss_r * (c * iss_u[2] + sn * iss_v[2])))

    for j in range(ISS_TRAIL):  # trail that fades out to the background colour
        (x1, y1, z1), (x2, y2, z2) = pts[j], pts[j + 1]
        if ((z1 + z2) >= 0) != front:
            continue
        fade = 0.9 * (1 - j / ISS_TRAIL)
        cv.create_line(x1, -y1, x2, -y2, fill=lerp_color(BG, ISS_TRAIL_COLOR, fade), width=2)

    x, y, z = pts[0]
    if (z >= 0) != front:
        return
    lvl = night_level(x)
    k = ISS_SIZE * (0.85 + 0.15 * z / iss_r)
    cy = -y
    truss, panel, body = ISS_TRUSS_SHADES[lvl], ISS_PANEL_SHADES[lvl], ISS_BODY_SHADES[lvl]
    cv.create_line(x - 10 * k, cy, x + 10 * k, cy, fill=truss, width=2)        # main truss
    for side in (-1, 1):                                                         # two pairs of arrays at the ends
        px = x + side * 10 * k
        for half in (-1, 1):
            y0 = cy + half * 1.2 * k
            cv.create_rectangle(px - 2.2 * k, y0, px + 2.2 * k, y0 + half * 8 * k,
                                fill=panel, outline="")
    cv.create_rectangle(x - 1.8 * k, cy - 4.5 * k, x + 1.8 * k, cy + 4.5 * k, fill=body, outline="")  # modules
    cv.create_rectangle(x - 4 * k, cy - 1.2 * k, x + 4 * k, cy + 1.2 * k, fill=body, outline="")      # node
    if ISS_LABEL:
        size = max(8, round(9 * (state.static_k or 1.0)))
        for dx, dy, color in ((1.2, 1.2, "#05080a"), (0, 0, "#d9dee5")):  # dark shadow so it stays readable over clouds
            cv.create_text(x + 14 * k + dx, cy - 11 * k + dy, text=ISS_LABEL, anchor="w", fill=color,
                           font=("Helvetica", size, "bold"))


# the outline of turtle.shape("turtle") from Python's turtle module: the nose is at (0, 16) and points "forward"
TURTLE_SHAPE = [(0, 16), (-2, 14), (-1, 10), (-4, 7), (-7, 9), (-9, 8), (-6, 5), (-7, 1), (-5, -3), (-8, -6),
                (-6, -8), (-4, -5), (0, -7), (4, -5), (6, -8), (8, -6), (5, -3), (7, 1), (6, 5), (9, 8),
                (7, 9), (4, 7), (1, 10), (2, 14)]


def player_path(sign, count, step):
    """Points on the turtle's CURRENT orbit: sign=+1 ahead of it, sign=-1 behind it."""
    p, t, r = player["p"], player["t"], player["alt"] * RADIUS
    pts = []
    for j in range(count + 1):
        c, sn = math.cos(sign * j * step), math.sin(sign * j * step)
        pts.append((r * (p[0] * c + t[0] * sn), r * (p[1] * c + t[1] * sn), r * (p[2] * c + t[2] * sn)))
    return pts


def draw_turtle(front):
    """The turtle, a dotted prediction of its orbit ahead and a trail behind. front=False - while it is behind
    the Earth (drawn before the globe, so the globe covers it); front=True - in front of it. While it is hidden
    behind the Earth a dim outline is drawn on top, so you never lose it."""
    pl = player
    x, y, z = player_pos()
    # the trail behind the turtle darkens on the night side along the same curve as everything else. It can cross
    # the day / night line, so each piece gets its own colour; neighbours of the same colour share one line
    pts = player_path(-1, 12, 0.05)
    run, run_color = None, None
    for (x1, y1, z1), (x2, y2, z2) in zip(pts, pts[1:]):
        if (z1 + z2 >= 0) != front:                 # this piece is on the other side of the globe
            if run:
                cv.create_line(run, fill=run_color, width=2)
            run = None
            continue
        color = lerp_color(PLAYER_TRAIL, PLAYER_TRAIL_NIGHT, night_factor((x1 + x2) / 2))
        if run and color == run_color:
            run += [x2, -y2]
        else:
            if run:
                cv.create_line(run, fill=run_color, width=2)
            run, run_color = [x1, -y1, x2, -y2], color
    if run:
        cv.create_line(run, fill=run_color, width=2)
    for near, flat in side_runs(player_path(1, 22, PLAYER_PATH / 22)):          # where this orbit leads
        if near == front and len(flat) >= 4:
            cv.create_line(flat, fill="#58c98a", width=1, dash=(2, 5))
    tx, ty = pl["t"][0], pl["t"][1]
    n = math.hypot(tx, ty)
    if n > 0.05:                                    # moving towards / away from the viewer: keep the last heading
        pl["head"] = (tx / n, ty / n)
    e0, e1 = pl["head"]
    if pl["wobble"] > 0:                            # tumbling after a hit
        a = 1.1 * math.sin(pl["wobble"] * 0.8) * pl["wobble"] / WOBBLE_LIFE
        e0, e1 = e0 * math.cos(a) - e1 * math.sin(a), e0 * math.sin(a) + e1 * math.cos(a)
    size = PLAYER_SIZE * (0.9 + 0.1 * z / (pl["alt"] * RADIUS))
    flat = []
    for sx, sy in TURTLE_SHAPE:                     # the same transform turtle uses: nose -> heading
        flat.append(x + (e1 * sx + e0 * sy) * size)
        flat.append(-(y + (-e0 * sx + e1 * sy) * size))
    blink = pl["hit"] > 0 and int(state.tick / 3) % 2 == 0
    if (z >= 0) == front:
        if not blink:
            dark = night_factor(x)   # 0 on the day side ... 1 in full night, the same curve the globe darkens along
            cv.create_polygon(flat, fill=lerp_color(PLAYER_COLOR, PLAYER_COLOR_NIGHT, dark),
                              outline=lerp_color(PLAYER_EDGE, PLAYER_EDGE_NIGHT, dark), width=1)
    elif front:
        cv.create_polygon(flat, fill="", outline="#3f9f6a", width=1)


def station_polys(x, y, k, ang=0.0):
    """The ISS as plain shapes around its centre (x, y) on the screen, turned by `ang`:
    [("truss", flat line), ("panel" | "body", flat polygon), ...]."""
    c, s = math.cos(ang), math.sin(ang)

    def rect(x0, y0, x1, y1):
        out = []
        for lx, ly in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            out += [x + (lx * c - ly * s) * k, y + (lx * s + ly * c) * k]
        return out

    shapes = [("truss", [x - 10 * k * c, y - 10 * k * s, x + 10 * k * c, y + 10 * k * s])]
    for side in (-1, 1):
        for half in (-1, 1):
            shapes.append(("panel", rect(side * 10 - 2.2, half * 1.2, side * 10 + 2.2, half * 1.2 + half * 8)))
    shapes.append(("body", rect(-1.8, -4.5, 1.8, 4.5)))
    shapes.append(("body", rect(-4, -1.2, 4, 1.2)))
    return shapes


def draw_wreck(w, front):
    """A caught station: it falls intact (turning orange as it nears the air), then burns inside ONE fireball that
    swells and shrinks while the station melts away. front=False: while it is behind the Earth (drawn before the
    globe, so the globe covers it); front=True: in front of it."""
    x, y, z = w["p"]
    if (z >= 0) != front:
        return
    phase, q = wreck_state(w, w["age"])[1:]
    depth = 0.85 + 0.15 * z / math.sqrt(x * x + y * y + z * z)
    cy = -y
    if phase == "fall":
        heat, shrink = 0.5 * clamp01((q - 0.6) / 0.4), 1.0 - 0.2 * q * q    # warming up; a little smaller as it drops away from us
    else:
        heat, shrink = 0.5 + 0.5 * q, 0.8 * (1.0 - 0.9 * q * q)            # glowing, and melting away
        rad = (5 + 20 * math.sin(math.pi * q) ** 0.7) * (1.0 + 0.07 * math.sin(w["age"] * 3.0))
        for scale, color in ((1.0, BURN_COLORS[3]), (0.72, BURN_COLORS[2]), (0.46, BURN_COLORS[1]), (0.22, BURN_COLORS[0])):
            r = rad * scale
            cv.create_oval(x - r, cy - r, x + r, cy + r, fill=color, outline="")
    k = ISS_SIZE * depth * shrink
    for kind, flat in station_polys(x, cy, k, 0.0):
        base = ISS_TRUSS if kind == "truss" else ISS_PANEL if kind == "panel" else ISS_BODY
        color = lerp_color(base, fire_color(0.3), heat)
        if kind == "truss":
            cv.create_line(flat, fill=color, width=2)
        else:
            cv.create_polygon(flat, fill=color, outline="")


def draw_burning(front):
    """The caught station(s) falling and burning."""
    for w in wrecks:
        draw_wreck(w, front)


def draw_game_overlay():
    """On top of everything (in the globe's coordinates): the capture ring around the ISS and the flashes."""
    pl = player
    if layer_on["iss"]:
        ix, iy, iz = iss_pos()
        px, py, pz = player_pos()
        close = dist((ix, iy, iz), (px, py, pz)) < HUD_CLOSE * CATCH_RADIUS
        r = CATCH_RADIUS * (1.0 + 0.08 * math.sin(state.tick * 0.3))
        color = "#7dffb0" if close else ("#ffd479" if iz >= 0 else "#8a6a30")
        cv.create_oval(ix - r, -iy - r, ix + r, -iy + r, outline=color, width=2, dash=(5, 4))
    for ex, ey, age, color in effects:
        f = age / EFFECT_LIFE
        r = 8 + 46 * f
        cv.create_oval(ex - r, -ey - r, ex + r, -ey + r, outline=lerp_color(color, BG, f),
                       width=max(1, round(4 * (1 - f))))
