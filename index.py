import base64
import math
import random
import struct
import time
import tkinter
import tkinter.font
import turtle
import zlib

# --- Settings ---
WIDTH, HEIGHT = 700, 800
RADIUS = 250
TILT = math.radians(23.5)   # axial tilt of the globe
SPEED = math.radians(0.3)   # rotation angle per frame
# Layers the user can switch on and off in the panel: (key, label)
LAYERS = [
    ("stars", "Stars"),
    ("atmo", "Atmosphere"),
    ("ocean", "Ocean"),
    ("land", "Continents"),
    ("night", "Day / night"),
    ("cities", "City lights"),
    ("clouds", "Clouds"),
    ("sats", "Satellites"),
    ("iss", "ISS"),
    ("game", "Game (turtle, score)"),
]
layer_on = {key: True for key, _ in LAYERS}  # current state of the checkboxes (cached, so frames never ask Tk)

TICK_MS = 25                # animation time unit: SPEED, PLAYER_SPEED, etc. are "per 25 ms" (= 40 steps/s)
SHOW_PANEL = True           # show the control panel (FPS + layer checkboxes) at start; H hides / shows it
AUTO_QUALITY = True         # on a slow machine, drop detail step by step until the animation runs smoothly
QUALITY_WINDOW = 90        # the decision is the MEDIAN of this many recent frames, so a single hiccup never counts
QUALITY_MIN_FPS = 40        # if the real frame rate stays below this, switch to the next (simpler) quality level
TARGET_FPS = 120            # frame rate to aim for (the speed of motion does NOT depend on it)
COAST_STEP = 4              # max step (degrees) when densifying outlines

BG = "#050a08"
OCEAN = "#21496b"           # colour of seas and oceans (same as the lowest atmosphere layer)
LAND_FILL = "#0d7a38"
LAND_EDGE = "#7dffb0"

# --- Night on the left hemisphere ---
LAND_NIGHT = "#010802"       # land in darkness
NIGHT_START = 0.10           # where the transition starts (fraction of radius from centre, + is right)
NIGHT_END = -0.15            # where the transition ends in full night (- is left)
NIGHT_STEPS = 14             # number of steps used to colour objects (satellites, city lights)
NIGHT_DARKNESS = 0.94        # how dark the night side gets (0 = not at all, 1 = pitch black)

# --- Atmosphere ---
ATMO_COLOR = "#4aa8ff"       # atmosphere colour
ATMO_WIDTH = 28              # halo thickness above the surface (pixels)
ATMO_STRENGTH = 0.40         # brightness near the surface (0..1)
ATMO_NIGHT = 0.06            # fraction of brightness left on the night side

# --- Clouds (fluffy, cumulus) ---
CLOUD_SYSTEMS = 15           # number of cloud clusters
CLOUD_HALO = "#c3d3e6"       # soft cloud edge
CLOUD_SHADOW = "#9fb2cb"     # grey-blue shadow underneath
CLOUD_BODY = "#f4f8fc"       # bright white top
CLOUD_VERTS = 10             # vertices per puff (fewer = faster)
CLOUD_CS = [(math.cos(2 * math.pi * v / CLOUD_VERTS), math.sin(2 * math.pi * v / CLOUD_VERTS))
            for v in range(CLOUD_VERTS)]
CLOUD_SCALE = 1.012          # clouds sit slightly above the surface
CLOUD_DRIFT = 1.15           # clouds rotate slightly faster than the surface

# --- Stars ---
STAR_COUNT = 98              # number of background stars
STAR_COLORS = ["#ffffff", "#cfe0ff", "#fff1d0"]
STAR_TWINKLE = 1.0           # brightness pulsing depth (0 - no pulsing, 1 - almost fade out)

# --- Satellites ---
SATELLITE_COUNT = 10         # most ordinary satellites that can fly at once (the game adds one per level, up to this)
SATELLITE_SEED = 5           # change the number to get a different set of orbits


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
SAT_TRAIL = 14               # trail length (number of segments)
TRAIL_GROUPS = 4              # a trail is drawn as this many polylines of decreasing brightness
SAT_TRAIL_STEP = 0.05        # angle between trail points (rad)
SAT_BODY, SAT_BODY_NIGHT = "#eef3f8", "#7d8590"      # body: day -> night
SAT_PANEL, SAT_PANEL_NIGHT = "#6fa8ff", "#2c4a75"    # solar panels
SAT_TRAIL_COLOR, SAT_TRAIL_NIGHT = "#8fb8ff", "#2f4560"  # trail

# --- ISS (International Space Station) ---
ISS_ORBIT = 1.18             # orbit radius in Earth radii (one of the turtle's altitude steps)
ISS_INCLINATION = 51.6       # orbit inclination to the equator, degrees (the real ISS inclination)
ISS_PHASE = 0.8              # initial position on the orbit
ISS_LABEL = ""               # label next to the station (e.g. "ISS"); empty string - no label
ISS_SIZE = 1.35              # size of the station icon
ISS_TRAIL = 22               # trail length
ISS_BODY, ISS_BODY_NIGHT = "#f4f6f8", "#8f98a3"      # modules
ISS_TRUSS, ISS_TRUSS_NIGHT = "#c9ced4", "#6c737c"    # truss
ISS_PANEL, ISS_PANEL_NIGHT = "#e2ab3c", "#7d5f22"    # solar arrays
ISS_TRAIL_COLOR = "#ffe7a6"

# --- Game: fly the turtle and catch the ISS ---
# One key press = one step; holding a key does NOT repeat it.
# Left / Right turn the turtle's orbit by PLAYER_TURN_STEP (a plane change); Up / Down raise / lower it by PLAYER_ALT_STEP.
CATCH_RADIUS = 30            # pixels: how close the turtle must get to the ISS to catch it
PLAYER_SPEED = 0.020         # orbital speed of the turtle at the reference altitude (rad per step)
PLAYER_REF_ALT = 1.22        # reference altitude, in Earth radii (the turtle starts here)
PLAYER_ALT_RANGE = (1.10, 1.34)  # lowest / highest orbit the turtle can fly (Earth radii): 7 altitude levels
PLAYER_TURN_STEP = math.radians(15)  # one Left / Right press turns the orbit by this angle
PLAYER_ALT_STEP = 0.04       # one Up / Down press changes the altitude by this much (Earth radii)
PLAYER_SIZE = 1.5            # size of the turtle
GLOBE_GAP = 24               # minimum free pixels between the globe and the HUD plate above it and the window edge below it
HUD_MARGIN = 32              # pixels between the score and the top / right edge of the picture (the same on both sides)
PLAYER_COLOR, PLAYER_EDGE = "#3ddc84", "#e9fff2"              # the turtle by day: shell, outline
PLAYER_COLOR_NIGHT, PLAYER_EDGE_NIGHT = "#04170b", "#0b3a1d"  # ... on the night side: dark green, almost black
PLAYER_TRAIL, PLAYER_TRAIL_NIGHT = "#3f9f6a", "#0b3a1d"       # the trail behind the turtle: by day, and on the night side
PLAYER_PATH = 1.5            # length of the dotted orbit prediction ahead of the turtle (rad)
BUMP_RADIUS = 18             # pixels: a satellite this close knocks the turtle off its orbit
BUMP_TURN = 0.30             # how far a hit turns the orbit (rad)
BUMP_LEVELS = (1,)             # a hit pushes the turtle up or down by this many altitude steps
BUMP_COOLDOWN = 45           # steps of immunity after a hit (the turtle blinks)
ISS_ALT_RANGE = (1.12, 1.32)     # altitude of a newly spawned ISS (Earth radii); always one of the turtle's altitude steps

# --- Difficulty: grows with every ISS you catch (level = score + 1) ---
# Level 1: only the ISS, and it hardly moves. Every next level adds ONE ordinary satellite (up to SATELLITE_COUNT)
# and makes the ISS faster. The ISS speed is a FRACTION of the turtle's own speed on the ISS's orbit, so it can never
# overtake the turtle: it starts at ISS_SPEED_START, grows by a big step first (ISS_SPEED_FIRST_STEP), then by smaller
# and smaller ones (each is ISS_SPEED_DECAY of the previous one, but never less than ISS_SPEED_MIN_STEP),
# and stops at ISS_SPEED_MAX (the limit itself is 1.0 = the turtle's speed).
ISS_SPEED_START = 0.05       # level 1: the station is almost standing still
ISS_SPEED_FIRST_STEP = 0.20  # speed gained going from level 1 to level 2
ISS_SPEED_DECAY = 0.70       # every next gain is this part of the previous one ...
ISS_SPEED_MIN_STEP = 0.05    # ... but never smaller than this
ISS_SPEED_MAX = 0.95         # the ISS never gets faster than this fraction of the turtle's speed on the same orbit
# --- The caught ISS burns up in the atmosphere ---
BURN_ANIMATION = True        # False: a caught station just disappears
BURN_FALL = 0.45             # seconds the station falls (from the highest orbit; a lower one falls for less, down to BURN_FALL_MIN)
BURN_FALL_MIN = 0.15         # seconds of falling from the lowest orbit
BURN_FIRE = 0.45             # seconds it burns in the air
BURN_DRIFT = 30              # pixels it drifts sideways along its orbit while falling (less for a slow station)
BURN_END = 5                 # pixels above the surface where it is gone (with a flash)
FORECAST_SECONDS = 15        # how far ahead the ETA / MIS instruments look

# --- City lights on the night side ---
CITY_COLOR = "#ffcf6e"       # colour of the lights
CITY_DOTS = 4                # number of smaller lights around each city
CITY_SPREAD = 0.7            # spread of lights around a city (degrees)
CITY_VISIBLE_FROM = 0.6      # how deep into the night (fraction of the gradient) the lights glow; higher = they switch off earlier

# --- Simplified outlines of continents and islands: (longitude, latitude) ---
CONTINENTS = {
    "North America": [
        (-168, 66), (-162, 70), (-156, 71.5), (-140, 70), (-128, 70), (-115, 68),
        (-95, 68), (-93, 62), (-94, 58), (-88, 56), (-82, 55), (-79, 52),
        (-78, 58), (-77, 62), (-72, 62), (-65, 60), (-62, 57), (-56, 52),
        (-60, 50), (-65, 49), (-67, 45), (-70, 43), (-70, 41.5), (-74, 40.5),
        (-76, 37), (-76, 35), (-81, 31), (-80, 26), (-81, 25.5), (-83, 29),
        (-85, 30), (-89, 30), (-91, 29), (-94, 29.5), (-97, 27), (-97.5, 22),
        (-96, 19), (-91, 19), (-90, 21), (-87, 21), (-88, 16), (-84, 15.5),
        (-83, 11), (-80, 9), (-77, 8.5), (-80, 7.5), (-83, 8), (-86, 11),
        (-87, 13), (-92, 14.5), (-96, 15.5), (-105, 20), (-106, 23), (-109, 26),
        (-112, 29), (-115, 30), (-117, 32.5), (-120.5, 34.5), (-122.5, 37.5),
        (-124, 40.5), (-124, 46), (-124.5, 48), (-123, 49), (-127, 51),
        (-130, 54), (-133, 57), (-137, 59), (-141, 60), (-148, 60.5),
        (-152, 59), (-158, 57), (-164, 55), (-158, 58.5), (-162, 60),
        (-166, 62), (-165, 64),
    ],
    "South America": [
        (-77, 8), (-72, 12), (-64, 10.5), (-60, 8.5), (-52, 5), (-50, 0),
        (-44, -2.5), (-35, -5.5), (-35, -9), (-39, -14), (-39, -18), (-41, -22),
        (-45, -23.5), (-48, -26), (-49, -29), (-53, -34), (-58, -34.5),
        (-57, -38), (-62, -39), (-65, -41), (-64, -45), (-67, -46.5),
        (-66, -48), (-69, -51), (-68.5, -53), (-71, -54), (-74, -52),
        (-75, -47), (-73.5, -42), (-73.5, -37), (-71.5, -30), (-70.5, -20),
        (-76, -14), (-81, -6), (-80, -2), (-79.5, 1), (-77.5, 4), (-77.5, 7.5),
    ],
    "Eurasia": [
        (-9, 37), (-9, 43), (-2, 43.5), (-4.5, 48.5), (2, 51), (8, 54), (8, 58),
        (5, 59), (5, 62), (14, 67), (20, 70), (28, 71), (33, 69), (41, 67),
        (44, 66), (53, 68), (60, 69), (68, 69), (73, 72), (80, 73), (90, 76),
        (105, 78), (112, 74), (130, 71), (140, 72), (160, 70), (170, 70),
        (180, 68), (180, 65), (172, 61), (163, 60), (163, 56), (156, 51),
        (155, 57), (143, 59), (137, 54), (141, 52), (140, 48), (133, 43),
        (129, 41), (129, 35), (126, 35), (125, 40), (121, 40), (122, 37),
        (119, 35), (121, 31), (122, 29), (117, 23), (110, 21), (108, 21.5),
        (106, 19), (109, 12), (105, 9), (103, 10), (100, 13), (99, 8),
        (103, 2), (101, 3), (98, 8), (98, 16), (94, 17), (92, 21), (88, 22),
        (86, 20), (80, 15), (80, 10), (77, 8), (73, 16), (72, 21), (67, 24),
        (62, 25), (57, 26), (56.5, 27), (52, 28), (48.5, 30), (50, 26),
        (51.5, 24), (56, 26), (59, 22.5), (55, 17), (52, 16), (45, 13),
        (43, 13), (39, 21), (35, 28), (34, 31), (36, 36), (30, 36), (27, 37),
        (26, 40.5), (24, 40), (23, 37), (21, 37.5), (19.5, 41), (19, 42),
        (13.5, 45.5), (12.5, 44), (16, 41.5), (18.5, 40), (16, 38), (15.5, 40),
        (12, 42), (9, 44), (3, 43), (0, 39), (-1, 37.5), (-5, 36),
    ],
    "Africa": [
        (-17, 21), (-17, 15), (-13, 9), (-8, 4.5), (-2, 5), (4, 6), (9, 4),
        (9.5, 1), (12, -5), (13, -12), (12, -17), (15, -27), (18, -34),
        (20, -35), (26, -34), (32, -28), (35, -24), (35, -20), (40, -15),
        (40, -10), (39, -5), (41, -2), (46, 2), (51, 11), (43, 12), (39, 16),
        (37, 22), (33, 28), (32, 31), (25, 32), (20, 31), (15, 32), (10, 34),
        (11, 37), (3, 37), (-2, 35), (-6, 36), (-9, 31), (-10, 28), (-14, 26),
    ],
    "Australia": [
        (114, -22), (114, -34), (118, -35), (124, -33.5), (131, -31.5),
        (138, -35), (141, -38), (147, -38.5), (150, -37), (153, -30),
        (153, -25), (146, -19), (142, -11), (140, -17), (136, -12), (130, -12),
        (127, -14), (122, -17),
    ],
    "Antarctica": [
        (-180, -78), (-150, -76), (-120, -74), (-100, -72), (-75, -72),
        (-65, -66), (-62, -64), (-57, -63.5), (-65, -68), (-70, -72),
        (-60, -75), (-50, -78), (-40, -78), (-30, -77), (-15, -72), (0, -70),
        (20, -70), (40, -68), (60, -67), (70, -68), (80, -67), (100, -66),
        (120, -66), (140, -67), (160, -70), (170, -72), (180, -78),
        (180, -90), (-180, -90),
    ],
    "Greenland": [
        (-73, 78), (-60, 82), (-30, 83.5), (-18, 80), (-20, 75), (-22, 70),
        (-33, 68), (-43, 60), (-48, 61), (-53, 67), (-55, 71), (-62, 76),
    ],
    "Great Britain": [
        (-5.5, 50), (1.5, 51), (0, 53), (-2, 56), (-2, 57.5), (-4, 58.6),
        (-6, 57), (-5, 55), (-3, 54), (-4.5, 52),
    ],
    "Ireland": [(-10, 52), (-6, 52), (-6, 55), (-8, 55)],
    "Iceland": [(-24, 65.5), (-18, 66.3), (-14, 65), (-18, 63.5), (-22, 64)],
    "Honshu": [
        (130.5, 31), (132, 34), (135, 33.5), (140, 35), (141, 38), (142, 40),
        (140, 41), (139.5, 38), (136.5, 37), (133, 35.5), (130.5, 33.5),
    ],
    "Hokkaido": [(140, 42), (143, 42), (145, 43.5), (142, 45.5), (141.5, 43.5)],
    "Sumatra": [(95, 5.5), (98, 4), (104, -1), (106, -6), (102, -4), (97, 1)],
    "Borneo": [
        (109, 1.5), (111, 2), (117, 7), (119, 5), (117, 1), (116, -4),
        (110, -3), (109, -1),
    ],
    "Java": [(105.5, -6.5), (114, -7.5), (114, -8.5), (106, -7.5)],
    "New Guinea": [
        (131, -1), (138, -2), (145, -5), (150, -10), (143, -9), (138, -8),
        (134, -4),
    ],
    "Madagascar": [(44, -25), (47, -25), (50, -15), (49, -12), (44, -17)],
    "New Zealand (north)": [
        (173, -35), (176, -37.5), (178, -38), (175, -41.5), (174.5, -39),
        (174, -37),
    ],
    "New Zealand (south)": [
        (172.5, -40.5), (174, -41.5), (171, -44.5), (169, -46.5), (166.5, -46),
        (170.5, -43),
    ],
}


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

def lerp_color(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


N = NIGHT_STEPS


def clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v


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


def png_rgba(w, h, rows):
    """Encodes RGBA rows (bytes) into a PNG - Tk can load it directly, no imaging library needed."""
    raw = b"".join(b"\x00" + row for row in rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 2)) + chunk(b"IEND", b""))


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


ATMO_TILES = 32  # the atmosphere ring is split into this many small images (tiny pixel area for Tk to blend)
XE = NIGHT_END * RADIUS    # left of this x it is full night (objects use plain dark colours there)
XS = NIGHT_START * RADIUS  # right of this x it is full day


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
        if max(c[0] for c in corners) <= XE:
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


STAR_WORLD = 1300            # half-size of the star "universe" (for large screens)


def make_stars():
    """Random (but always identical) stars outside the globe and its atmosphere.
    First the same set as in the normal window, then stars of the same density beyond its edges."""
    rnd = random.Random(3)
    half_w, half_h = WIDTH / 2 - 8, HEIGHT / 2 - 8
    near = RADIUS + ATMO_WIDTH + 8
    area_in = (2 * half_w) * (2 * half_h)
    extra = round(STAR_COUNT * ((2 * STAR_WORLD) ** 2 - area_in) / area_in)

    def star(x, y):
        return (x, y, rnd.choice([0.5, 0.6, 0.6, 0.8, 1.0]), rnd.choice(STAR_COLORS),
                rnd.uniform(0, 2 * math.pi), rnd.uniform(0.008, 0.025))

    stars = []
    while len(stars) < STAR_COUNT:
        x, y = rnd.uniform(-half_w, half_w), rnd.uniform(-half_h, half_h)
        if math.hypot(x, y) >= near:
            stars.append(star(x, y))
    while len(stars) < STAR_COUNT + extra:
        x, y = rnd.uniform(-STAR_WORLD, STAR_WORLD), rnd.uniform(-STAR_WORLD, STAR_WORLD)
        if abs(x) >= half_w or abs(y) >= half_h:
            stars.append(star(x, y))
    return stars


STARS = make_stars()


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / n, v[1] / n, v[2] / n)


def make_orbits():
    """Basis of each orbit plane: position = r·(cosθ·u + sinθ·v)."""
    orbits = []
    for factor, normal, omega, phase in SATELLITES:
        n = _unit(normal)
        ref = (0.0, 1.0, 0.0) if abs(n[1]) < 0.9 else (1.0, 0.0, 0.0)
        u = _unit(_cross(n, ref))
        v = _cross(n, u)
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
    u = _unit(_cross(n, ref))
    v = _cross(n, u)
    return ISS_ORBIT * RADIUS, u, v


ISS_R, ISS_U, ISS_V = make_iss()
ISS_BODY_SHADES = [lerp_color(ISS_BODY, ISS_BODY_NIGHT, t / N) for t in range(N + 1)]
ISS_TRUSS_SHADES = [lerp_color(ISS_TRUSS, ISS_TRUSS_NIGHT, t / N) for t in range(N + 1)]
ISS_PANEL_SHADES = [lerp_color(ISS_PANEL, ISS_PANEL_NIGHT, t / N) for t in range(N + 1)]
tick = 0
view_hw, view_hh = WIDTH / 2, HEIGHT / 2  # visible area in "world" coordinates
view_box = [-WIDTH / 2, -HEIGHT / 2, WIDTH / 2, HEIGHT / 2]  # the same area in screen pixels: left, top, right, bottom


# ------------------------------------------------------------------ game logic
def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def orbit_basis(n):
    """Two perpendicular unit vectors spanning the plane with normal n: position = r * (cos a * u + sin a * v)."""
    n = _unit(n)
    ref = (0.0, 1.0, 0.0) if abs(n[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = _unit(_cross(n, ref))
    return u, _cross(n, u)


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
score = 0


def level():
    """Game level = number of caught ISS + 1."""
    return score + 1


def active_satellites():
    """How many ordinary satellites are flying: none on level 1, then one more per level (up to SATELLITE_COUNT).
    With the game switched off all of them fly (the plain screensaver)."""
    if not layer_on["game"]:
        return len(ORBITS)
    return min(len(ORBITS), level() - 1)
_p0 = _unit((-0.55, -0.25, 0.8))
player = {
    "p": _p0,                                  # unit vector from the Earth's centre to the turtle
    "t": _unit(_cross((0.0, 1.0, 0.0), _p0)),  # unit velocity direction (perpendicular to p)
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


def rotate_heading(p, t, angle):
    """Turns the velocity direction t about the radial axis p. That is a plane change of the orbit.
    angle > 0 turns left (seen from outside the globe), angle < 0 turns right."""
    c, s = math.cos(angle), math.sin(angle)
    w = _cross(p, t)
    return _unit((t[0] * c + w[0] * s, t[1] * c + w[1] * s, t[2] * c + w[2] * s))


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
        if _dist(pos, avoid) > 170:
            break
    iss.update(r=r, u=u, v=v, omega=iss_omega(alt, level()), theta=theta)


def satellite_positions():
    """Positions of the ordinary satellites that are flying right now (see active_satellites)."""
    out = []
    for r, u, v, omega, phase in ORBITS[:active_satellites()]:
        c, s = math.cos(phase + omega * tick), math.sin(phase + omega * tick)
        out.append((r * (c * u[0] + s * v[0]), r * (c * u[1] + s * v[1]), r * (c * u[2] + s * v[2])))
    return out


def activate_satellite(index, avoid):
    """A new level brings satellite number `index`: it appears on its own orbit, but never right on top of the
    turtle (its position on the orbit is re-rolled until it is more than 160 px away from `avoid`)."""
    r, u, v, omega, phase = ORBITS[index]
    for _ in range(80):
        phase = game_rng.uniform(0, 2 * math.pi)
        c, s = math.cos(phase + omega * tick), math.sin(phase + omega * tick)
        pos = (r * (c * u[0] + s * v[0]), r * (c * u[1] + s * v[1]), r * (c * u[2] + s * v[2]))
        if _dist(pos, avoid) > 160:
            break
    ORBITS[index] = (r, u, v, omega, phase)
    effects.append([pos[0], pos[1], 0.0, "#8fb8ff"])  # a blue ring marks where it appeared


def bump_player(sat):
    """A satellite hit: the orbit is knocked slightly off - the velocity turns away from the satellite and
    the altitude changes a little (away from the satellite's altitude)."""
    pl = player
    p, t = pl["p"], pl["t"]
    rel = _sub(sat, player_pos())
    side = _dot(_cross(p, t), rel)                      # > 0: the satellite is on the turtle's left
    if abs(side) < 1e-6:
        side = game_rng.choice((-1.0, 1.0))
    pl["t"] = rotate_heading(p, t, -math.copysign(BUMP_TURN * game_rng.uniform(0.7, 1.3), side))
    pushed_down = math.sqrt(_dot(sat, sat)) > pl["alt"] * RADIUS
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
    r0 = math.sqrt(_dot(pos, pos))
    tangent = _unit(tuple(-s * u[i] + c * v[i] for i in range(3)))         # the direction it was flying
    drift = min(BURN_DRIFT, r * iss["omega"] * 20)                         # what it would cover in half a second
    span = max(1.0, ISS_ALT_RANGE[1] * RADIUS - R_ATM)
    high = clamp01((r0 - R_ATM) / span)                                    # 0 = just above the air, 1 = the highest orbit
    per_s = 1000.0 / TICK_MS
    t_fall = per_s * (BURN_FALL_MIN + (BURN_FALL - BURN_FALL_MIN) * high)
    wrecks.append({"u0": _mul(pos, 1.0 / r0), "r0": r0, "drift": _mul(tangent, drift), "age": 0.0, "p": pos,
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
    n = math.sqrt(_dot(d, d)) or 1.0
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
    global score
    pl = player
    p, t, alt = pl["p"], pl["t"], pl["alt"]
    phi = turtle_speed(alt) * steps                                # lower orbits are faster
    c, s = math.cos(phi), math.sin(phi)
    p, t = _unit(_add(_mul(p, c), _mul(t, s))), _add(_mul(t, c), _mul(p, -s))
    t = _unit(_sub(t, _mul(p, _dot(t, p))))                        # keep t exactly perpendicular to p
    pl["p"], pl["t"] = p, t
    pl["hit"] = max(0.0, pl["hit"] - steps)
    pl["wobble"] = max(0.0, pl["wobble"] - steps)
    pos = player_pos()

    if layer_on["iss"] and _dist(pos, iss_pos()) < CATCH_RADIUS:
        score += 1
        ix, iy, _ = iss_pos()
        effects.append([ix, iy, 0.0, "#7dffb0"])
        if BURN_ANIMATION:
            start_burn()                                 # the caught station falls and burns up (see update_burn)
        spawn_iss(pos)                                   # faster than before: it already uses the new level
        if level() - 1 <= len(ORBITS):                   # this level brings one more ordinary satellite
            activate_satellite(level() - 2, pos)
    if layer_on["sats"] and pl["hit"] <= 0:
        for sat in satellite_positions():
            if _dist(sat, pos) < BUMP_RADIUS:
                bump_player(sat)
                break

    update_burn(steps)
    for e in effects:
        e[2] += steps
    effects[:] = [e for e in effects if e[2] < EFFECT_LIFE]


ARROWS = ("Left", "Right", "Up", "Down")
KEY_ACTIONS = {"Left": (turn_player, 1), "Right": (turn_player, -1), "Up": (climb_player, 1), "Down": (climb_player, -1)}
release_jobs = {}


def on_key_press(event):
    """One press = one step. A key that is already down is auto-repeating: it is ignored, so holding does nothing."""
    key = event.keysym
    if key not in ARROWS:
        return
    job = release_jobs.pop(key, None)
    if job:
        root.after_cancel(job)
    if key in keys_held:
        return  # auto-repeat of a held key
    keys_held.add(key)
    if layer_on["game"]:
        action, sign = KEY_ACTIONS[key]
        action(sign)


def on_key_release(event):
    key = event.keysym
    if key in ARROWS:
        # some systems auto-repeat as release + press pairs: the key only counts as released if no press
        # follows within 30 ms (a real second tap is much slower than that)
        def let_go(k=key):
            keys_held.discard(k)
            release_jobs.pop(k, None)
        release_jobs[key] = root.after(30, let_go)

# Major cities: (latitude, longitude)
CITIES = [
    # North America
    (40.7, -74.0), (42.4, -71.1), (38.9, -77.0), (41.9, -87.6), (33.7, -84.4), (25.8, -80.2),
    (32.8, -96.8), (29.8, -95.4), (39.7, -105.0), (33.4, -112.0), (34.0, -118.2), (37.8, -122.4),
    (47.6, -122.3), (49.3, -123.1), (43.7, -79.4), (45.5, -73.6), (19.4, -99.1), (20.7, -103.3),
    (25.7, -100.3), (9.0, -79.5),
    # South America
    (4.7, -74.1), (-12.0, -77.0), (-0.2, -78.5), (10.5, -66.9), (-23.5, -46.6), (-22.9, -43.2),
    (-15.8, -47.9), (-19.9, -43.9), (-8.0, -34.9), (-13.0, -38.5), (-34.6, -58.4), (-33.4, -70.7),
    (-34.9, -56.2), (-16.5, -68.1), (-3.7, -38.5), (-3.1, -60.0),
    # Europe
    (51.5, -0.1), (48.9, 2.3), (40.4, -3.7), (41.4, 2.2), (38.7, -9.1), (41.9, 12.5), (45.5, 9.2),
    (52.5, 13.4), (52.4, 4.9), (50.8, 4.4), (50.1, 8.7), (48.1, 11.6), (48.2, 16.4), (50.1, 14.4),
    (52.2, 21.0), (47.5, 19.0), (38.0, 23.7), (41.0, 29.0), (50.4, 30.5), (55.8, 37.6), (59.9, 30.3),
    (59.3, 18.1), (59.9, 10.7), (60.2, 25.0), (55.7, 12.6), (44.4, 26.1), (53.9, 27.6), (50.0, 36.2),
    (46.5, 30.7), (48.5, 35.0), (49.8, 24.0),
    # Africa
    (30.0, 31.2), (6.5, 3.4), (-4.3, 15.3), (-26.2, 28.0), (-33.9, 18.4), (-1.3, 36.8), (9.0, 38.7),
    (33.6, -7.6), (36.8, 3.1), (36.8, 10.2), (5.6, -0.2), (14.7, -17.4), (15.6, 32.5), (-8.8, 13.2),
    (-6.8, 39.3), (-29.9, 31.0), (5.3, -4.0), (32.9, 13.2), (-26.0, 32.6),
    # Asia
    (35.7, 51.4), (33.3, 44.4), (24.7, 46.7), (25.2, 55.3), (24.9, 67.0), (31.5, 74.3), (28.6, 77.2),
    (19.1, 72.9), (22.6, 88.4), (13.0, 77.6), (13.1, 80.3), (17.4, 78.5), (23.8, 90.4), (13.8, 100.5),
    (21.0, 105.8), (10.8, 106.7), (3.1, 101.7), (14.6, 121.0), (39.9, 116.4), (31.2, 121.5),
    (23.1, 113.3), (22.5, 114.1), (29.6, 106.5), (30.7, 104.0), (30.6, 114.3), (34.3, 108.9),
    (39.1, 117.2), (37.6, 127.0), (35.7, 139.7), (34.7, 135.5), (35.2, 136.9), (43.1, 141.4),
    (55.0, 82.9), (56.8, 60.6), (43.1, 131.9), (41.3, 69.3), (43.2, 76.9), (34.5, 69.2),
    (47.9, 106.9), (16.8, 96.2),
    # Oceania
    (-33.9, 151.2), (-37.8, 145.0), (-27.5, 153.0), (-32.0, 115.9), (-34.9, 138.6), (-36.8, 174.8),
]


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

# --- Window ---
screen = turtle.Screen()
screen.setup(WIDTH, HEIGHT)
screen.screensize(WIDTH - 40, HEIGHT - 40)  # canvas slightly smaller than the window: (0, 0) stays centred, no scrollbars
screen.bgcolor(BG)
screen.title("Spinning Earth  -  Arrows: fly the turtle, F: fullscreen, H: panel, Esc: quit")
screen.tracer(0)
cv = screen.getcanvas()  # draw directly on the tkinter canvas - faster than turtle
_tcl, _cw = cv.tk.call, cv._canvas._w


def tk_poly(flat, color):
    """Filled polygon via a direct Tcl call (about 2x cheaper than cv.create_polygon, which parses options)."""
    _tcl(_cw, "create", "polygon", *flat, "-fill", color, "-outline", "")


def line(flat, color, width):
    _tcl(_cw, "create", "line", *flat, "-fill", color, "-width", width)


def rect(x0, y0, x1, y1, color):
    _tcl(_cw, "create", "rectangle", x0, y0, x1, y1, "-fill", color, "-outline", "")
root = cv.winfo_toplevel()
fullscreen = False
last_size = None
quality = 0          # 0 = everything ... 3 = minimal (only ever goes down; resets when the window size changes)
recent = []          # real intervals (ms) between the last frames
quality_wait = 60    # frames to wait (start-up, or after a change) before judging again
static_k = None   # scale the static layer was built for (None = not built yet)
static_dy = None  # ... and how far below the canvas centre it put the globe (screen pixels)
static_imgs = []  # keeps the PhotoImage objects alive
last_time = None
MAX_STEPS = 4.0  # after a pause (e.g. dragging the window) the animation never jumps by more than 4 steps


def set_fullscreen(on):
    global fullscreen
    fullscreen = on
    root.attributes("-fullscreen", on)


def toggle_fullscreen(event=None):
    set_fullscreen(not fullscreen)


def exit_fullscreen(event=None):
    if fullscreen:
        set_fullscreen(False)


for key in ("<f>", "<F>", "<F11>"):
    root.bind(key, toggle_fullscreen)
cv.bind("<Double-Button-1>", toggle_fullscreen, add="+")  # on the canvas only: a fast double click on a checkbox must not toggle fullscreen
root.bind("<Escape>", exit_fullscreen)
root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)
root.bind("<FocusOut>", lambda e: keys_held.clear())  # never leave a key "stuck" when the window loses focus


def fit_to_window():
    """Fits the canvas to the window size and returns the scale (1 = original size)."""
    global last_size, view_hw, view_hh
    ic = cv._canvas  # the canvas widget itself: its real visible edges, not the size of the frame around it
    view_box[:] = [ic.canvasx(0), ic.canvasy(0), ic.canvasx(ic.winfo_width()), ic.canvasy(ic.winfo_height())]
    w, h = max(2, cv.winfo_width()), max(2, cv.winfo_height())
    if (w, h) != last_size:
        last_size = (w, h)
        screen.screensize(max(100, w - 40), max(100, h - 40))  # (0, 0) stays centred
    k = min(w, h) / WIDTH
    if layer_on["game"]:
        # the globe (with its glow) must fit in the space BELOW the HUD plate, with GLOBE_GAP free on both sides.
        # The plate's size depends on the scale, so refine twice.
        for _ in range(2):
            room = h - HUD_MARGIN - hud_metrics(k)[-1] - 2 * GLOBE_GAP
            k = min(k, room / (2 * (RADIUS + ATMO_WIDTH)))
        k = max(k, 0.2)
    if abs(k - 1) < 0.05:
        k = 1.0
    view_hw, view_hh = w / 2 / k, h / 2 / k
    return k

angle = 0.0


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
    if min(xs) >= XE:
        fill(poly, day)
    elif max(xs) <= XE:
        fill(poly, night)
    else:
        fill(clip_left(poly, XE), night)
        fill(clip_right(poly, XE), day)


def fill(poly, color):
    if len(poly) >= 3:
        flat = []
        for x, y in poly:
            flat.append(x)
            flat.append(-y)
        tk_poly(flat, color)


def night_level(x):
    """0 = day, N = full night (for x in pixels)."""
    if not layer_on["night"]:
        return 0
    f = (NIGHT_START * RADIUS - x) / ((NIGHT_START - NIGHT_END) * RADIUS)
    return max(0, min(N, round(f * N)))


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
                night = (x1 + x2) < 2 * XE
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


star_items = []      # (canvas item, x, y, size, colour, phase, speed) in screen pixels
STAR_UPDATE_EVERY = 6  # twinkling changes slowly, so stars are updated every few frames only
last_star_tick = -100.0


def build_stars(k):
    """Stars are persistent canvas items (created with the static layer) - they cost nothing between updates."""
    star_items.clear()
    for x, y, size, color, phase, speed in STARS:
        if abs(x) > view_hw or abs(y) > view_hh:
            continue  # outside the visible area (relevant for fullscreen)
        item = cv.create_oval((x - size) * k, (-y - size) * k, (x + size) * k, (-y + size) * k,
                              fill=color, outline="", tags=("static", "stars"))
        star_items.append((item, x * k, -y * k, size * k, color, phase, speed))


def update_stars():
    global last_star_tick
    if quality >= 1 or not layer_on["stars"]:
        return  # no twinkling on a slow machine (or while the stars are switched off)
    if tick - last_star_tick < STAR_UPDATE_EVERY:
        return
    last_star_tick = tick
    for item, x, y, size, color, phase, speed in star_items:
        b = 1 - STAR_TWINKLE * (0.5 + 0.5 * math.sin(tick * speed + phase))  # 1 = brightest, 0 = almost faded out
        r = size * (0.7 + 0.3 * b)  # the star "breathes" slightly along with its brightness
        cv.coords(item, x - r, y - r, x + r, y + r)
        cv.itemconfigure(item, fill=lerp_color(BG, color, 0.06 + 0.94 * b))


def scaled(pts, mx, my, k, dy):
    return [(mx + (x - mx) * k, my + (y - my) * k + dy) for x, y in pts]


def draw_cities(rot):
    """City lights: glow only on the night side, flicker slightly, hidden by clouds."""
    if quality >= 3:
        return
    cr, sr = math.cos(rot), math.sin(rot)
    for cl, sl, slon, clon, size, core, phase in CITY_LIGHTS:
        if quality >= 2 and not core:
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
        glow *= (0.85 + 0.15 * math.sin(tick * 0.03 + phase)) * (z ** 0.4)
        idx = int(min(1.0, glow) * CITY_LEVELS)
        if idx == 0:
            continue
        b = size * (0.6 + 0.4 * z)
        if core:  # soft glow around the city centre
            rect(x - b * 1.9, -y - b * 1.9, x + b * 1.9, -y + b * 1.9, CITY_SHADES[max(1, idx // 3)])
        rect(x - b, -y - b, x + b, -y + b, CITY_SHADES[idx])


def draw_satellites(front):
    """Satellites with trails. front=False - those behind the Earth (drawn before the globe, so the globe covers them)."""
    for r, u, v, omega, phase in ORBITS[:active_satellites()]:
        direction = 1 if omega > 0 else -1
        theta = phase + omega * tick
        pts = []
        for j in range(SAT_TRAIL + 1):
            t = theta - direction * j * SAT_TRAIL_STEP
            c, sn = math.cos(t), math.sin(t)
            pts.append((r * (c * u[0] + sn * v[0]),
                        r * (c * u[1] + sn * v[1]),
                        r * (c * u[2] + sn * v[2])))

        # trail: a few polylines that fade out to the background colour (not one item per step)
        group, run = -1, None
        for j in range(0 if quality >= 2 else SAT_TRAIL):
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
        size = max(8, round(9 * (static_k or 1.0)))
        for dx, dy, color in ((1.2, 1.2, "#05080a"), (0, 0, "#d9dee5")):  # dark shadow so it stays readable over clouds
            cv.create_text(x + 14 * k + dx, cy - 11 * k + dy, text=ISS_LABEL, anchor="w", fill=color,
                           font=("Helvetica", size, "bold"))


# the outline of turtle.shape("turtle") from Python's turtle module: the nose is at (0, 16) and points "forward"
TURTLE_SHAPE = [(0, 16), (-2, 14), (-1, 10), (-4, 7), (-7, 9), (-9, 8), (-6, 5), (-7, 1), (-5, -3), (-8, -6),
                (-6, -8), (-4, -5), (0, -7), (4, -5), (6, -8), (8, -6), (5, -3), (7, 1), (6, 5), (9, 8),
                (7, 9), (4, 7), (1, 10), (2, 14)]


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
    blink = pl["hit"] > 0 and int(tick / 3) % 2 == 0
    if (z >= 0) == front:
        if not blink:
            dark = night_factor(x)   # 0 on the day side ... 1 in full night, the same curve the globe darkens along
            cv.create_polygon(flat, fill=lerp_color(PLAYER_COLOR, PLAYER_COLOR_NIGHT, dark),
                              outline=lerp_color(PLAYER_EDGE, PLAYER_EDGE_NIGHT, dark), width=1)
    elif front:
        cv.create_polygon(flat, fill="", outline="#3f9f6a", width=1)


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
    iu = _unit(iss_pos())
    d = _sub(iu, _mul(p, _dot(iu, p)))
    if _dot(d, d) < 1e-12:
        return 0.0
    d = _unit(d)
    return math.degrees(math.atan2(_dot(_cross(p, t), d), _dot(t, d)))


HUD_COLUMNS = (("ALT", 6), ("SPD", 6), ("DST", 6), ("BRG", 6), ("ETA", 6), ("MIS", 5))  # (header, width in characters)
HUD_LABEL_WIDTH = 4
HUD_CLOSE, HUD_AIM = 2.5, 10   # DST turns green within HUD_CLOSE catch radii; BRG within HUD_AIM degrees of straight ahead
HUD_TEXT, HUD_DIM, HUD_GREEN, HUD_AMBER = "#dbe4ee", "#8a99a8", "#7dffb0", "#ffd479"
hud_fonts = {}


def hud_font(size):
    """(font, character width, line height) of the HUD's monospaced font at this size; cached."""
    if size not in hud_fonts:
        font = tkinter.font.Font(root=root, family="Courier", size=size, weight="bold")
        hud_fonts[size] = (font, font.measure("0"), font.metrics("linespace"))
    return hud_fonts[size]


def hud_metrics(k):
    """Fonts and sizes of the HUD plate at scale k: (table font, its character width, its line height, title font,
    its character width, its line height, padding, table row height, plate height) - all in screen pixels.
    The HUD never grows with the window: in fullscreen or a big window it keeps its normal size (k is capped at 1);
    it only shrinks in a window smaller than the standard one, so that it does not cover the whole picture."""
    k = min(k, 1.0)
    table_font, cw, lh = hud_font(max(8, round(11 * k)))
    title_font, tcw, tlh = hud_font(max(10, round(18 * k)))
    pad, row_h = round(10 * k), round(lh * 1.2)
    plate_h = pad + tlh + round(lh * 1.3) + 3 * row_h + pad
    return table_font, cw, lh, title_font, tcw, tlh, pad, row_h, plate_h


def globe_shift(k):
    """How many screen pixels BELOW the canvas centre the globe's centre sits. With the HUD on, the globe is
    centred between the bottom of the HUD plate and the bottom edge of the window (equal free space above and
    below it) instead of between the top and the bottom edge. It is never pushed so low that its glow would be
    cut off by the bottom edge, and never up. Without the HUD (game off) the globe is simply centred."""
    left, top, right, bottom = view_box
    if not layer_on["game"]:
        return int(round((top + bottom) / 2))      # the true middle of the visible area
    hud_bottom = top + HUD_MARGIN + hud_metrics(k)[-1]
    centre = (hud_bottom + bottom) / 2
    lowest = bottom - (RADIUS + ATMO_WIDTH) * k - 2
    return int(round(min(centre, lowest)))


def draw_hud():
    """Top-right panel: score, level and a table of instruments. Drawn in screen pixels, after the globe has been
    scaled and shifted, so the plate stays put while the globe is centred below it.

    Rows: the ISS and the turtle (TUR). Columns:
      ALT  altitude, Earth radii (green on both when they are within one altitude step - you can catch it)
      SPD  orbital speed, degrees per second
      DST  distance turtle - ISS, px (green when it is within 2.5 catch radii)
      BRG  where the ISS is relative to your heading: L = left, R = right, in degrees (green when almost ahead)
      ETA  seconds until the closest approach if you press nothing, MIS = the distance then, px.
           MIS below the catch radius (green) means you are on a collision course and will catch it."""
    pl = player
    k = static_k or 1.0
    iss_alt = iss["r"] / RADIUS
    eta, miss = intercept_forecast()
    bearing = iss_bearing()
    dst = _dist(iss_pos(), player_pos())
    per_s = 1000.0 / TICK_MS
    aligned = abs(pl["alt"] - iss_alt) <= PLAYER_ALT_STEP * 1.01
    course = HUD_GREEN if miss < CATCH_RADIUS else (HUD_AMBER if miss < 2 * CATCH_RADIUS else HUD_TEXT)
    if abs(bearing) < 0.5:
        brg = "0\u00b0"
    else:
        brg = "%s%d\u00b0" % ("L" if bearing > 0 else "R", round(abs(bearing)))
    alt_color = HUD_GREEN if aligned else HUD_TEXT
    rows = (
        ("ISS", HUD_AMBER, [
            ("%.2f" % iss_alt, alt_color),
            ("%.1f" % math.degrees(iss["omega"] * per_s), HUD_TEXT),
            ("%d" % round(dst), HUD_GREEN if dst < HUD_CLOSE * CATCH_RADIUS else HUD_TEXT),
            (brg, HUD_GREEN if abs(bearing) < HUD_AIM else HUD_TEXT),
            ("--" if eta is None else "%.1fs" % eta, HUD_DIM if eta is None else course),
            ("%d" % round(miss), course)]),
        ("TUR", PLAYER_COLOR, [
            ("%.2f" % pl["alt"], alt_color),
            ("%.1f" % math.degrees(turtle_speed(pl["alt"]) * per_s), HUD_TEXT),
            ("-", HUD_DIM), ("-", HUD_DIM), ("-", HUD_DIM), ("-", HUD_DIM)]),
    )

    table_font, cw, lh, title_font, tcw, tlh, pad, row_h, plate_h = hud_metrics(k)
    title = "SCORE: %04d" % score
    info = "LVL %02d   SAT %02d" % (level(), active_satellites())
    table_w = (HUD_LABEL_WIDTH + sum(w for _, w in HUD_COLUMNS)) * cw
    plate_w = max(table_w, len(title) * tcw) + 2 * pad
    left, top, right, bottom = view_box              # the real visible edges of the canvas, in screen pixels
    x1, y0 = right - HUD_MARGIN, top + HUD_MARGIN    # the plate is the same distance from the right and the top edge
    x0, y1 = x1 - plate_w, y0 + plate_h

    cv.create_rectangle(x0, y0, x1, y1, fill="#0a1017", outline="#26323f")
    tx, ty = x0 + pad, y0 + pad
    cv.create_text(tx, ty, text=title, anchor="nw", fill=HUD_GREEN, font=title_font)
    ty += tlh
    cv.create_text(tx, ty, text=info, anchor="nw", fill=HUD_DIM, font=table_font)
    ty += round(lh * 1.3)
    right_edge = [tx + (HUD_LABEL_WIDTH + sum(w for _, w in HUD_COLUMNS[:j]) + w - 1) * cw
                  for j, (_, w) in enumerate(HUD_COLUMNS)]   # right edge of each column (one character is the gap)
    for (name, _), x in zip(HUD_COLUMNS, right_edge):
        cv.create_text(x, ty, text=name, anchor="ne", fill=HUD_DIM, font=table_font)
    ty += row_h
    for label, label_color, cells in rows:
        cv.create_text(tx, ty, text=label, anchor="nw", fill=label_color, font=table_font)
        for (text, color), x in zip(cells, right_edge):
            cv.create_text(x, ty, text=text, anchor="ne", fill=color, font=table_font)
        ty += row_h


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
        close = _dist((ix, iy, iz), (px, py, pz)) < HUD_CLOSE * CATCH_RADIUS
        r = CATCH_RADIUS * (1.0 + 0.08 * math.sin(tick * 0.3))
        color = "#7dffb0" if close else ("#ffd479" if iz >= 0 else "#8a6a30")
        cv.create_oval(ix - r, -iy - r, ix + r, -iy + r, outline=color, width=2, dash=(5, 4))
    for ex, ey, age, color in effects:
        f = age / EFFECT_LIFE
        r = 8 + 46 * f
        cv.create_oval(ex - r, -ey - r, ex + r, -ey + r, outline=lerp_color(color, BG, f),
                       width=max(1, round(4 * (1 - f))))


def draw_clouds(rot):
    """Fluffy clouds: soft edge, shadow underneath, white top; they darken at night along with the surface.
    Each puff is projected once (its centre); its outline is then laid out with the local east/north
    directions, which also gives the foreshortening near the limb for free."""
    rot = tick * SPEED * CLOUD_DRIFT  # does not reset after a full revolution
    update_clouds(rot)
    if quality >= 3:
        return
    cr, sr = math.cos(rot), math.sin(rot)
    scale = RADIUS * CLOUD_SCALE
    puffs = []
    step = 2 if quality >= 2 else 1  # slow machine: a FIXED half of every cluster (its puffs never change)
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
    for f, shift, day, night in (layers[1:] if quality >= 1 else layers):
        for cx, cy, ax, ay, bx, by, hy, hx in puffs:
            fax, fbx, fay, fby = f * ax, f * bx, f * ay, f * by
            ym = -(cy + shift * hy)
            flat = [0.0] * (2 * CLOUD_VERTS)
            flat[0::2] = [cx + fax * c + fbx * s for c, s in cs]
            flat[1::2] = [ym - fay * c - fby * s for c, s in cs]
            if cx - f * hx >= XE:
                tk_poly(flat, day)
            elif cx + f * hx <= XE:
                tk_poly(flat, night)
            else:  # crosses the full-night line: split in two
                pts = [(flat[i], -flat[i + 1]) for i in range(0, len(flat), 2)]
                fill(clip_left(pts, XE), night)
                fill(clip_right(pts, XE), day)


def build_static(k, dy=0):
    """Builds the layers that do not change between frames and tags them "static":
    atmosphere tiles, the ocean (a plain oval + its dark part) and the narrow night-gradient strip.
    dy = how many screen pixels below the canvas centre the globe's centre is put (see globe_shift)."""
    global static_k, static_dy, static_imgs, last_star_tick, XE
    # the "full night" line is exactly where the gradient strip begins, so land, clouds and the dark ocean all
    # switch to night colours on the same pixel column; with the night layer off there is no such line at all
    XE = math.ceil(NIGHT_END * RADIUS * k) / k if layer_on["night"] else -1e9
    cv.delete("all")
    static_imgs = []
    build_stars(k)  # stars go first = they are at the very bottom
    last_star_tick = -100.0
    for x0, y0, png in make_atmo_tiles(k):
        img = tkinter.PhotoImage(master=root, data=base64.b64encode(png))
        static_imgs.append(img)
        cv.create_image(x0, y0 + dy, image=img, anchor="nw", tags=("static", "atmo"))
    r = RADIUS * k
    cv.create_oval(-r, -r + dy, r, r + dy, fill=OCEAN, outline="", tags=("static", "ocean"))
    circle = [(RADIUS * math.cos(2 * math.pi * i / 360), RADIUS * math.sin(2 * math.pi * i / 360)) for i in range(360)]
    x0, top, width, height, png = make_night_strip(k)
    if layer_on["night"]:
        dark = clip_left(circle, XE)
        cv.create_polygon([c for p in dark for c in (p[0] * k, -p[1] * k + dy)], fill=OCEAN_DARK, outline="",
                          tags=("static", "ocean"))
    img = tkinter.PhotoImage(master=root, data=base64.b64encode(png))
    static_imgs.append(img)
    cv.create_image(x0, -top + dy, image=img, anchor="nw", tags=("static", "shade"))
    static_k, static_dy = k, dy


def apply_visibility():
    """Shows or hides the persistent canvas items: a layer is visible if its checkbox is ticked AND the
    automatic quality level has not dropped it.
    Quality level 1: no cloud halo, no star twinkle. 2: half the clouds, no satellite trails, only the main city
    lights, no atmosphere glow. 3: no clouds, no city lights, no stars."""
    def state(on):
        return "normal" if on else "hidden"
    cv.itemconfigure("stars", state=state(layer_on["stars"] and quality < 3))
    cv.itemconfigure("atmo", state=state(layer_on["atmo"] and quality < 2))
    cv.itemconfigure("ocean", state=state(layer_on["ocean"]))
    cv.itemconfigure("shade", state=state(layer_on["night"]))


def adapt_quality(interval_ms):
    """Watches the real frame intervals and, if the machine cannot keep up, lowers the quality one level.
    It uses the median of the last QUALITY_WINDOW frames: a one-off stall (window drag, a system hiccup,
    the slow first frames) cannot trigger it, only a consistently low frame rate can."""
    global quality, quality_wait
    if not AUTO_QUALITY or quality >= 3:
        return
    recent.append(interval_ms)
    if len(recent) > QUALITY_WINDOW:
        del recent[0]
    quality_wait -= 1
    if quality_wait <= 0 and len(recent) >= QUALITY_WINDOW \
            and sorted(recent)[len(recent) // 2] > 1000.0 / QUALITY_MIN_FPS:
        quality += 1
        quality_wait = QUALITY_WINDOW
        recent.clear()
        apply_visibility()


def draw_frame():
    global angle, tick, last_time, quality, quality_wait
    started = time.perf_counter()
    update_fps(started)
    if last_time is not None and started - last_time < 0.5:
        adapt_quality((started - last_time) * 1000)
    # animation depends on real time, not on the frame count:
    # rotation speed is the same in a window and in fullscreen (where frames take longer to draw)
    steps = 1.0 if last_time is None else min(MAX_STEPS, (started - last_time) * 1000 / TICK_MS)
    last_time = started
    global static_k
    k = fit_to_window()
    dy = globe_shift(k)               # the globe is centred between the HUD and the bottom of the window
    if k != static_k or dy != static_dy:
        if static_k is not None and k != static_k:   # window size changed: judge the quality again from scratch
            quality, quality_wait = 0, 60
            recent.clear()
        build_static(k, dy)
        apply_visibility()            # static layer (atmosphere and ocean) is drawn once and again on resize
    else:
        cv.delete("dyn")              # the rest of the frame is redrawn every time
    iss["theta"] += iss["omega"] * steps   # the ISS flies on its own orbit (also when the game is switched off)
    if layer_on["game"]:
        update_game(steps)
    elif wrecks:
        wrecks.clear()                # the game was switched off: nothing is left burning
    update_stars()                    # twinkle the (persistent) background stars
    if layer_on["sats"]:
        draw_satellites(front=False)  # satellites behind the Earth
    if layer_on["iss"]:
        draw_iss(front=False)         # ISS when it is behind the Earth
    if layer_on["game"]:
        draw_turtle(front=False)      # the turtle while it is behind the Earth
        draw_burning(front=False)     # a burning station behind the Earth
    cv.addtag_all("behind")           # everything behind the Earth is lowered beneath the static layer (atmosphere and ocean)
    cv.dtag("static", "behind")
    cv.tag_lower("behind")
    if layer_on["land"]:
        draw_land(angle)              # continents
    if layer_on["clouds"]:
        draw_clouds(angle)            # clouds
    else:
        update_clouds(tick * SPEED * CLOUD_DRIFT)  # keep the cloud systems moving so they are in place when switched on
    cv.tag_raise("shade")             # night shade over the land and clouds (city lights, satellites go above it)
    if layer_on["cities"] and layer_on["night"]:
        draw_cities(angle)            # city lights on the night side
    if layer_on["sats"]:
        draw_satellites(front=True)   # satellites in front of the Earth
    if layer_on["iss"]:
        draw_iss(front=True)          # ISS in front of the Earth
    if layer_on["game"]:
        draw_turtle(front=True)       # the turtle in front of the Earth (+ a dim outline while it is hidden)
        draw_burning(front=True)      # a burning station in front of the Earth, over the night shade (it is a light source)
        draw_game_overlay()           # ISS target ring, flashes and the score

    cv.addtag_all("dyn")              # tag everything drawn in this frame
    cv.dtag("static", "dyn")
    if k != 1.0:
        cv.scale("dyn", 0, 0, k, k)   # scale the image together with the window
    if dy:
        cv.move("dyn", 0, dy)         # and put it where the static layer put the globe
    if layer_on["game"]:
        draw_hud()                    # the HUD is drawn last, in screen pixels: it neither scales nor moves with the globe
        cv.addtag_all("dyn")
        cv.dtag("static", "dyn")

    angle = (angle + SPEED * steps) % (2 * math.pi)
    tick += steps
    spent = (time.perf_counter() - started) * 1000
    screen.ontimer(draw_frame, max(1, int(1000 / TARGET_FPS - spent)))  # aim for TARGET_FPS if we can keep up


PANEL_BG, PANEL_FG = "#0d141c", "#dbe4ee"
GRAPHICS_NAMES = ["full", "reduced", "low", "minimal"]
layer_vars = {}
panel_visible = SHOW_PANEL
fps_frames, fps_since = 0, time.perf_counter()
panel_width = 0


def on_layer_toggle(key):
    global static_k
    layer_on[key] = bool(layer_vars[key].get())
    if key == "night":
        static_k = None  # night changes the atmosphere dimming and the full-night line: rebuild the static layers
    else:
        apply_visibility()


def on_auto_toggle():
    global AUTO_QUALITY, quality, quality_wait
    AUTO_QUALITY = bool(auto_var.get())
    recent.clear()
    quality_wait = 60
    if not AUTO_QUALITY and quality:
        quality = 0  # switched off by the user = full graphics again: restore everything that was dropped
        apply_visibility()


def resize_window_by(dx):
    """Grows / shrinks the window by dx pixels (not in fullscreen), so the globe area keeps its size."""
    if not fullscreen:
        root.update_idletasks()
        root.geometry("%dx%d" % (root.winfo_width() + dx, root.winfo_height()))


def toggle_panel(event=None):
    """Shows / hides the side panel. It sits NEXT to the canvas, not on top of it: native widgets lying over a
    canvas that is redrawn every frame make the OS recompose them constantly (measured: ~25 FPS slower)."""
    global panel_visible
    panel_visible = not panel_visible
    if panel_visible:
        panel.pack(side="left", fill="y", before=cv)
        resize_window_by(panel_width)
    else:
        panel.pack_forget()
        resize_window_by(-panel_width)


# What every HUD value means, for the side panel: (name, colour of the name, explanation). The numbers come from the
# same constants the HUD itself uses, so this text cannot drift away from the game.
HUD_LEGEND = [
    ("LVL", HUD_DIM, "level = caught ISS + 1"),
    ("SAT", HUD_DIM, "satellites flying now"),
    ("ISS", HUD_AMBER, "the station you chase"),
    ("TUR", PLAYER_COLOR, "your turtle"),
    ("ALT", HUD_TEXT, "altitude; green = within 1 level, catchable"),
    ("SPD", HUD_TEXT, "orbital speed, degrees per second"),
    ("DST", HUD_TEXT, "distance to the ISS, px; green < %d" % round(HUD_CLOSE * CATCH_RADIUS)),
    ("BRG", HUD_TEXT, "L / R + degrees; green < %d = ahead" % HUD_AIM),
    ("ETA", HUD_TEXT, "secs to closest pass (no keys); -- = apart"),
    ("MIS", HUD_TEXT, "miss, px; green < %d = hit, amber < %d" % (CATCH_RADIUS, 2 * CATCH_RADIUS)),
]
LEGEND_WRAP = 262  # pixels: an explanation longer than this wraps instead of making the side panel wider


def build_panel():
    """Control panel in a column left of the canvas: FPS, one checkbox per layer, and the auto-quality checkbox."""
    global panel, fps_label, graphics_label, auto_var, panel_width
    panel = tkinter.Frame(root, bg=PANEL_BG, padx=14, pady=12)
    look = dict(bg=PANEL_BG, fg=PANEL_FG, activebackground=PANEL_BG, activeforeground=PANEL_FG,
                selectcolor=PANEL_BG, highlightthickness=0, bd=0, anchor="w", font=("Helvetica", 12))
    fps_label = tkinter.Label(panel, text="-- FPS", bg=PANEL_BG, fg="#7dffb0", anchor="w",
                              font=("Helvetica", 18, "bold"))
    fps_label.pack(anchor="w")
    graphics_label = tkinter.Label(panel, text="Graphics: full", bg=PANEL_BG, fg="#8a99a8", anchor="w",
                                   font=("Helvetica", 11))
    graphics_label.pack(anchor="w", pady=(0, 6))
    tkinter.Label(panel, text="LAYERS", bg=PANEL_BG, fg="#8a99a8", anchor="w", font=("Helvetica", 10, "bold")).pack(anchor="w")
    for key, label in LAYERS:
        layer_vars[key] = tkinter.BooleanVar(master=root, value=layer_on[key])
        tkinter.Checkbutton(panel, text=label, variable=layer_vars[key],
                            command=lambda k=key: on_layer_toggle(k), **look).pack(fill="x")
    tkinter.Frame(panel, bg="#26323f", height=1).pack(fill="x", pady=6)
    auto_var = tkinter.BooleanVar(master=root, value=AUTO_QUALITY)
    tkinter.Checkbutton(panel, text="Auto-reduce graphics", variable=auto_var, command=on_auto_toggle,
                        **look).pack(fill="x")
    tkinter.Frame(panel, bg="#26323f", height=1).pack(fill="x", pady=6)
    tkinter.Label(panel, text="GAME", bg=PANEL_BG, fg="#8a99a8", anchor="w", font=("Helvetica", 10, "bold")).pack(anchor="w")
    tkinter.Label(panel, text="Catch the ISS with the turtle.\nLeft / Right - turn the orbit (%d deg)\nUp / Down - raise / lower it (one step)\nEach catch: faster ISS + one more satellite" % round(math.degrees(PLAYER_TURN_STEP)),
                  bg=PANEL_BG, fg=PANEL_FG, justify="left", anchor="w", font=("Helvetica", 11)).pack(anchor="w")
    tkinter.Frame(panel, bg="#26323f", height=1).pack(fill="x", pady=6)
    tkinter.Label(panel, text="HUD (top right)", bg=PANEL_BG, fg="#8a99a8", anchor="w",
                  font=("Helvetica", 10, "bold")).pack(anchor="w")
    legend = tkinter.Frame(panel, bg=PANEL_BG)
    legend.pack(anchor="w", fill="x")
    for row, (name, color, text) in enumerate(HUD_LEGEND):
        tkinter.Label(legend, text=name, bg=PANEL_BG, fg=color, anchor="nw", font=("Courier", 11, "bold")).grid(
            row=row, column=0, sticky="nw", padx=(0, 8), pady=1)
        tkinter.Label(legend, text=text, bg=PANEL_BG, fg=PANEL_FG, anchor="w", justify="left", wraplength=LEGEND_WRAP,
                      font=("Helvetica", 10)).grid(row=row, column=1, sticky="w", pady=1)
    tkinter.Label(panel, text="H - hide panel", bg=PANEL_BG, fg="#5b6b7b", anchor="w",
                  font=("Helvetica", 10)).pack(anchor="w", pady=(6, 0))
    root.update_idletasks()
    panel_width = panel.winfo_reqwidth()
    if panel_visible:
        panel.pack(side="left", fill="y", before=cv)
        screen.setup(WIDTH + panel_width, HEIGHT)  # widen the window by the panel: the globe area stays WIDTH wide


def update_fps(now):
    """Refreshes the FPS readout twice a second (not every frame - label updates are not free)."""
    global fps_frames, fps_since
    fps_frames += 1
    if now - fps_since >= 0.5:
        if panel_visible:
            fps_label.config(text="%d FPS" % round(fps_frames / (now - fps_since)))
            graphics_label.config(text="Graphics: " + GRAPHICS_NAMES[quality] + (" (auto)" if quality else ""))
        fps_frames, fps_since = 0, now


for key in ("<h>", "<H>"):
    root.bind(key, toggle_panel)
build_panel()
draw_frame()
screen.mainloop()
