"""The game: the turtle, the ISS, levels, collisions, the forecast behind the ETA / MIS instruments and the burning of
a caught station. Logic only: nothing here draws."""

import math
import random

from earth import state
from earth.config import (
    ATMO_WIDTH, BUMP_COOLDOWN, BUMP_LEVELS, BUMP_RADIUS, BUMP_TURN, BURN_ANIMATION, BURN_DRIFT, BURN_END,
    BURN_FALL, BURN_FALL_MIN, BURN_FIRE, CATCH_RADIUS, FORECAST_SECONDS, ISS_ALT_RANGE, ISS_ORBIT, ISS_PHASE,
    ISS_SPEED_DECAY, ISS_SPEED_FIRST_STEP, ISS_SPEED_MAX, ISS_SPEED_MIN_STEP, ISS_SPEED_START,
    PLAYER_ALT_RANGE, PLAYER_ALT_STEP, PLAYER_REF_ALT, PLAYER_SPEED, PLAYER_TURN_STEP, RADIUS, TICK_MS,
)
from earth.state import layer_on
from earth.util import add, clamp01, cross, dist, dot, lerp_color, mul, orbit_basis, sub, unit
from earth.orbits import ISS_R, ISS_U, ISS_V, ORBITS


def turtle_speed(alt):
    """The turtle's orbital speed (rad per step) at altitude alt (Earth radii): lower orbits are faster (Kepler)."""
    return PLAYER_SPEED * (PLAYER_REF_ALT / alt) ** 1.5


def iss_speed_fraction(lvl):
    """The ISS speed on level lvl as a fraction of the turtle's speed on the same orbit:
    ISS_SPEED_START, then big steps that shrink (ISS_SPEED_FIRST_STEP * ISS_SPEED_DECAY ** n, at least
    ISS_SPEED_MIN_STEP) until ISS_SPEED_MAX."""
    fraction, step = ISS_SPEED_START, ISS_SPEED_FIRST_STEP
    for _ in range(lvl - 1):
        fraction = min(ISS_SPEED_MAX, fraction + step)
        step = max(ISS_SPEED_MIN_STEP, step * ISS_SPEED_DECAY)
    return fraction


def iss_omega(alt, lvl):
    """The ISS orbital speed (rad per step) at altitude alt (Earth radii) on level lvl."""
    return iss_speed_fraction(lvl) * turtle_speed(alt)


# the ISS is the game target: its orbit is replaced by a new random one every time it is caught
iss = {"r": ISS_R, "u": ISS_U, "v": ISS_V, "omega": iss_omega(ISS_ORBIT, 1), "theta": ISS_PHASE}
game_rng = random.Random()  # not seeded: every run gets different orbits


def level():
    """Game level = number of caught ISS + 1."""
    return state.score + 1


def active_satellites():
    """How many ordinary satellites are flying: none on level 1, then one more per level (up to SATELLITE_COUNT).
    With the game switched off all of them fly (the plain screensaver)."""
    if not layer_on["game"]:
        return len(ORBITS)
    return min(len(ORBITS), level() - 1)


_p0 = unit((-0.55, -0.25, 0.8))
player = {
    "p": _p0,                                  # unit vector from the Earth's centre to the turtle
    "t": unit(cross((0.0, 1.0, 0.0), _p0)),    # unit velocity direction (perpendicular to p)
    "alt": PLAYER_REF_ALT,                     # orbit radius in Earth radii
    "head": (1.0, 0.0),                        # last good on-screen heading (for drawing)
    "hit": 0.0,                                # steps of immunity left after a collision
    "wobble": 0.0,                             # steps of tumbling left after a collision
}
effects = []                                   # [x, y, age, colour] flashes (capture / collision)
EFFECT_LIFE = 26.0
WOBBLE_LIFE = 30.0
keys_held = set()                              # arrow keys that are physically down right now


def iss_pos():
    c, s = math.cos(iss["theta"]), math.sin(iss["theta"])
    r, u, v = iss["r"], iss["u"], iss["v"]
    return (r * (c * u[0] + s * v[0]), r * (c * u[1] + s * v[1]), r * (c * u[2] + s * v[2]))


def player_pos():
    p, r = player["p"], player["alt"] * RADIUS
    return (p[0] * r, p[1] * r, p[2] * r)


def rotate_heading(p, t, radians):
    """Turns the velocity direction t about the radial axis p. That is a plane change of the orbit.
    radians > 0 turns left (seen from outside the globe), radians < 0 turns right."""
    c, s = math.cos(radians), math.sin(radians)
    w = cross(p, t)
    return unit((t[0] * c + w[0] * s, t[1] * c + w[1] * s, t[2] * c + w[2] * s))


def alt_levels():
    """All altitudes the turtle can fly (Earth radii): PLAYER_ALT_RANGE in steps of PLAYER_ALT_STEP."""
    lo, hi = PLAYER_ALT_RANGE
    return [lo + i * PLAYER_ALT_STEP for i in range(int(round((hi - lo) / PLAYER_ALT_STEP)) + 1)]


def iss_altitudes():
    """The altitudes a new ISS can appear at: the turtle's steps inside ISS_ALT_RANGE (so they can be matched exactly)."""
    lo, hi = ISS_ALT_RANGE
    return [a for a in alt_levels() if lo - 1e-9 <= a <= hi + 1e-9]


def turn_player(sign):
    """One Left (+1) / Right (-1) press: turns the orbit by PLAYER_TURN_STEP."""
    pl = player
    pl["t"] = rotate_heading(pl["p"], pl["t"], sign * PLAYER_TURN_STEP)


def climb_player(sign):
    """One Up (+1) / Down (-1) press: moves the orbit one altitude step up / down (snapped to the altitude grid)."""
    lo, hi = PLAYER_ALT_RANGE
    level = int(round((player["alt"] - lo) / PLAYER_ALT_STEP)) + sign
    player["alt"] = min(hi, max(lo, lo + level * PLAYER_ALT_STEP))


def spawn_iss(avoid):
    """Puts the ISS on a new random orbit, at least ~170 px away from the point `avoid` (the turtle)."""
    rnd = game_rng
    for _ in range(40):
        u, v = orbit_basis((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)))
        alt = rnd.choice(iss_altitudes())
        r = alt * RADIUS
        theta = rnd.uniform(0, 2 * math.pi)
        c, s = math.cos(theta), math.sin(theta)
        pos = (r * (c * u[0] + s * v[0]), r * (c * u[1] + s * v[1]), r * (c * u[2] + s * v[2]))
        if dist(pos, avoid) > 170:
            break
    iss.update(r=r, u=u, v=v, omega=iss_omega(alt, level()), theta=theta)


def satellite_positions():
    """Positions of the ordinary satellites that are flying right now (see active_satellites)."""
    out = []
    for r, u, v, omega, phase in ORBITS[:active_satellites()]:
        c, s = math.cos(phase + omega * state.tick), math.sin(phase + omega * state.tick)
        out.append((r * (c * u[0] + s * v[0]), r * (c * u[1] + s * v[1]), r * (c * u[2] + s * v[2])))
    return out


def activate_satellite(index, avoid):
    """A new level brings satellite number `index`: it appears on its own orbit, but never right on top of the
    turtle (its position on the orbit is re-rolled until it is more than 160 px away from `avoid`)."""
    r, u, v, omega, phase = ORBITS[index]
    for _ in range(80):
        phase = game_rng.uniform(0, 2 * math.pi)
        c, s = math.cos(phase + omega * state.tick), math.sin(phase + omega * state.tick)
        pos = (r * (c * u[0] + s * v[0]), r * (c * u[1] + s * v[1]), r * (c * u[2] + s * v[2]))
        if dist(pos, avoid) > 160:
            break
    ORBITS[index] = (r, u, v, omega, phase)
    effects.append([pos[0], pos[1], 0.0, "#8fb8ff"])  # a blue ring marks where it appeared


def bump_player(sat):
    """A satellite hit: the orbit is knocked slightly off - the velocity turns away from the satellite and
    the altitude changes a little (away from the satellite's altitude)."""
    pl = player
    p, t = pl["p"], pl["t"]
    rel = sub(sat, player_pos())
    side = dot(cross(p, t), rel)                        # > 0: the satellite is on the turtle's left
    if abs(side) < 1e-6:
        side = game_rng.choice((-1.0, 1.0))
    pl["t"] = rotate_heading(p, t, -math.copysign(BUMP_TURN * game_rng.uniform(0.7, 1.3), side))
    pushed_down = math.sqrt(dot(sat, sat)) > pl["alt"] * RADIUS
    for _ in range(game_rng.choice(BUMP_LEVELS)):
        climb_player(-1 if pushed_down else 1)
    pl["hit"], pl["wobble"] = BUMP_COOLDOWN, WOBBLE_LIFE
    x, y, _ = player_pos()
    effects.append([x, y, 0.0, "#ff9a3c"])


# ----------------------------------------------------------------- the caught ISS burns up
# Two short phases, both a plain formula of time (so it is the same on any computer and any frame rate):
#   FALL  the station drops from where it was caught to the top of the air, faster and faster;
#   FIRE  it burns in the air, sinking slowly, inside a fireball that swells and shrinks, until it is gone.
BURN_COLORS = ["#fff7d6", "#ffd36b", "#ff8a2a", "#d83a12", "#5a1408"]  # white-hot ... a cooling ember
R_ATM = RADIUS + ATMO_WIDTH      # the top of the air: the fire starts when the station reaches this
R_END = RADIUS + BURN_END
wrecks = []                      # caught stations that are falling / burning


def fire_color(f):
    """Colour of burning metal: f = 0 white-hot ... f = 1 a cooled ember."""
    f = clamp01(f) * (len(BURN_COLORS) - 1)
    i = min(len(BURN_COLORS) - 2, int(f))
    return lerp_color(BURN_COLORS[i], BURN_COLORS[i + 1], f - i)


def start_burn():
    """The player has just caught the station: it starts to fall from where it was. Call this BEFORE the ISS is
    respawned. A station caught on a higher orbit has a longer way down, so it falls for longer."""
    th, r, u, v = iss["theta"], iss["r"], iss["u"], iss["v"]
    c, s = math.cos(th), math.sin(th)
    pos = iss_pos()
    r0 = math.sqrt(dot(pos, pos))
    tangent = unit(tuple(-s * u[i] + c * v[i] for i in range(3)))          # the direction it was flying
    drift = min(BURN_DRIFT, r * iss["omega"] * 20)                         # what it would cover in half a second
    span = max(1.0, ISS_ALT_RANGE[1] * RADIUS - R_ATM)
    high = clamp01((r0 - R_ATM) / span)                                    # 0 = just above the air, 1 = the highest orbit
    per_s = 1000.0 / TICK_MS
    t_fall = per_s * (BURN_FALL_MIN + (BURN_FALL - BURN_FALL_MIN) * high)
    wrecks.append({"u0": mul(pos, 1.0 / r0), "r0": r0, "drift": mul(tangent, drift), "age": 0.0, "p": pos,
                   "t_fall": t_fall, "t_fire": per_s * BURN_FIRE})


def wreck_state(w, age):
    """Where the wreck is `age` steps after the catch and in which phase: ((x, y, z), phase, progress 0..1).
    Falling is ease-in (it accelerates), burning is ease-out (the air slows it down)."""
    t_fall, t_fire = w["t_fall"], w["t_fire"]
    if age < t_fall:
        phase, q = "fall", age / t_fall
        r = w["r0"] + (R_ATM - w["r0"]) * q * q
    else:
        q = clamp01((age - t_fall) / t_fire)
        phase = "fire"
        r = R_ATM + (R_END - R_ATM) * (1.0 - (1.0 - q) ** 2)
    s = clamp01(age / (t_fall + t_fire))
    e = 1.0 - (1.0 - s) ** 2                                               # the sideways drift slows down too
    d = tuple(w["u0"][i] * w["r0"] + w["drift"][i] * e for i in range(3))
    n = math.sqrt(dot(d, d)) or 1.0
    return (d[0] / n * r, d[1] / n * r, d[2] / n * r), phase, q


def update_burn(steps):
    """Advances every wreck by `steps` animation steps; a wreck whose time is up ends with a flash."""
    for w in wrecks[:]:
        w["age"] += steps
        w["p"] = wreck_state(w, w["age"])[0]
        if w["age"] >= w["t_fall"] + w["t_fire"]:
            effects.append([w["p"][0], w["p"][1], 0.0, "#ff9a3c"])         # it is burnt out: a flash
            wrecks.remove(w)


def update_game(steps):
    """Moves the turtle along its orbit (Kepler-style: lower = faster), then checks the catch and the hits.
    Steering and altitude are NOT handled here: they change only on key presses (see on_key_press)."""
    pl = player
    p, t, alt = pl["p"], pl["t"], pl["alt"]
    phi = turtle_speed(alt) * steps                                # lower orbits are faster
    c, s = math.cos(phi), math.sin(phi)
    p, t = unit(add(mul(p, c), mul(t, s))), add(mul(t, c), mul(p, -s))
    t = unit(sub(t, mul(p, dot(t, p))))                            # keep t exactly perpendicular to p
    pl["p"], pl["t"] = p, t
    pl["hit"] = max(0.0, pl["hit"] - steps)
    pl["wobble"] = max(0.0, pl["wobble"] - steps)
    pos = player_pos()

    if layer_on["iss"] and dist(pos, iss_pos()) < CATCH_RADIUS:
        state.score += 1
        ix, iy, _ = iss_pos()
        effects.append([ix, iy, 0.0, "#7dffb0"])
        if BURN_ANIMATION:
            start_burn()                                 # the caught station falls and burns up (see update_burn)
        spawn_iss(pos)                                   # faster than before: it already uses the new level
        if level() - 1 <= len(ORBITS):                   # this level brings one more ordinary satellite
            activate_satellite(level() - 2, pos)
    if layer_on["sats"] and pl["hit"] <= 0:
        for sat in satellite_positions():
            if dist(sat, pos) < BUMP_RADIUS:
                bump_player(sat)
                break

    update_burn(steps)
    for e in effects:
        e[2] += steps
    effects[:] = [e for e in effects if e[2] < EFFECT_LIFE]


def intercept_forecast():
    """If nothing changes (no key is pressed), where do the turtle and the ISS go? Both keep flying their current
    orbits. Returns (seconds until they are closest, the distance in px at that moment); the time is None when
    they only move apart from now on. If the turtle would catch the ISS (come within CATCH_RADIUS), it reports the
    FIRST such pass, not a later closer one."""
    pl = player
    p, t, rt = pl["p"], pl["t"], pl["alt"] * RADIUS
    wt = turtle_speed(pl["alt"])
    wi, ri, u, v, th = iss["omega"], iss["r"], iss["u"], iss["v"], iss["theta"]

    def gap(tau):                                   # distance after tau steps
        c, s = math.cos(wt * tau), math.sin(wt * tau)
        cb, sb = math.cos(th + wi * tau), math.sin(th + wi * tau)
        dx = rt * (p[0] * c + t[0] * s) - ri * (u[0] * cb + v[0] * sb)
        dy = rt * (p[1] * c + t[1] * s) - ri * (u[1] * cb + v[1] * sb)
        dz = rt * (p[2] * c + t[2] * s) - ri * (u[2] * cb + v[2] * sb)
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    horizon, coarse = FORECAST_SECONDS * 1000.0 / TICK_MS, 4.0
    samples = [gap(i * coarse) for i in range(int(horizon / coarse) + 1)]   # coarse scan: every 4 steps = 0.1 s
    best_tau, best = 0.0, samples[0]
    first_catch = None                              # the earliest pass that gets inside the catch zone
    for i, d in enumerate(samples):
        # a close pass is sharp (the objects move ~10 px per step), so a coarse sample can miss its bottom:
        # look closer around EVERY local minimum, not only the lowest sample
        left = samples[i - 1] if i > 0 else float("inf")
        right = samples[i + 1] if i + 1 < len(samples) else float("inf")
        if d <= left and d <= right:
            lo, hi = max(0.0, (i - 1) * coarse), min(horizon, (i + 1) * coarse)   # never look beyond the horizon
            pass_tau, pass_min = lo, float("inf")
            for j in range(33):
                tau = lo + j * (hi - lo) / 32
                dd = gap(tau)
                if dd < pass_min:
                    pass_tau, pass_min = tau, dd
            if pass_min < best:
                best_tau, best = pass_tau, pass_min
            if first_catch is None and pass_min < CATCH_RADIUS:
                first_catch = (pass_tau, pass_min)
    if first_catch is not None:
        # If the first pass already catches the ISS, that is the one that matters (the ISS disappears when it is
        # caught), even when a later lap would pass a hair closer. Without this a station standing exactly on the
        # turtle's path (two passes of ~0 px) could show the SECOND lap, decided by floating-point noise.
        best_tau, best = first_catch
    return (best_tau * TICK_MS / 1000.0 if best_tau > 0 else None), best


def iss_bearing():
    """Where the ISS is relative to the turtle's heading, in degrees: > 0 = to the left, < 0 = to the right,
    0 = dead ahead, 180 = behind (measured along the surface, in the tangent plane at the turtle)."""
    p, t = player["p"], player["t"]
    iu = unit(iss_pos())
    d = sub(iu, mul(p, dot(iu, p)))
    if dot(d, d) < 1e-12:
        return 0.0
    d = unit(d)
    return math.degrees(math.atan2(dot(cross(p, t), d), dot(t, d)))
