import math
import random
import time
import turtle

# --- Settings ---
WIDTH, HEIGHT = 700, 700
RADIUS = 250
TILT = math.radians(23.5)   # axial tilt of the globe
SPEED = math.radians(0.3)   # rotation angle per frame
FRAME_MS = 25               # ~40 frames/s
COAST_STEP = 4              # max step (degrees) when densifying outlines

BG = "#050a08"
OCEAN = "#21496b"           # colour of seas and oceans (same as the lowest atmosphere layer)
LAND_FILL = "#0d7a38"
LAND_EDGE = "#7dffb0"

# --- Night on the left hemisphere ---
OCEAN_NIGHT = "#010206"      # ocean in darkness
LAND_NIGHT = "#010802"       # land in darkness
EDGE_NIGHT = "#041a0b"       # coastlines in darkness
NIGHT_START = 0.10           # where the transition starts (fraction of radius from centre, + is right)
NIGHT_END = -0.15            # where the transition ends in full night (- is left)
NIGHT_STEPS = 14             # number of gradient steps

# --- Atmosphere ---
ATMO_COLOR = "#4aa8ff"       # atmosphere colour
ATMO_WIDTH = 28              # halo thickness above the surface (pixels)
ATMO_RINGS = 12              # number of halo layers (more = smoother)
ATMO_STRENGTH = 0.40         # brightness near the surface (0..1)
ATMO_NIGHT = 0.06            # fraction of brightness left on the night side

# --- Clouds (fluffy, cumulus) ---
CLOUD_SYSTEMS = 15           # number of cloud clusters
CLOUD_HALO = "#c3d3e6"       # soft cloud edge
CLOUD_SHADOW = "#9fb2cb"     # grey-blue shadow underneath
CLOUD_BODY = "#f4f8fc"       # bright white top
CLOUD_BODY_NIGHT = "#131415"  # cloud top at night (neutral grey)
CLOUD_SHADOW_NIGHT = "#0a0b0c"
CLOUD_HALO_NIGHT = "#070809"
CLOUD_SCALE = 1.012          # clouds sit slightly above the surface
CLOUD_DRIFT = 1.15           # clouds rotate slightly faster than the surface

# --- Stars ---
STAR_COUNT = 98              # number of background stars
STAR_COLORS = ["#ffffff", "#cfe0ff", "#fff1d0"]
STAR_TWINKLE = 1.0           # brightness pulsing depth (0 - no pulsing, 1 - almost fade out)

# --- Satellites ---
SATELLITE_COUNT = 10         # number of satellites
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
SAT_TRAIL_STEP = 0.05        # angle between trail points (rad)
SAT_BODY, SAT_BODY_NIGHT = "#eef3f8", "#7d8590"      # body: day -> night
SAT_PANEL, SAT_PANEL_NIGHT = "#6fa8ff", "#2c4a75"    # solar panels
SAT_TRAIL_COLOR, SAT_TRAIL_NIGHT = "#8fb8ff", "#2f4560"  # trail

# --- ISS (International Space Station) ---
ISS_ORBIT = 1.15             # orbit radius in Earth radii (lower than the other satellites)
ISS_INCLINATION = 51.6       # orbit inclination to the equator, degrees (the real ISS inclination)
ISS_SPEED = 0.026            # orbital speed, rad/frame
ISS_PHASE = 0.8              # initial position on the orbit
ISS_LABEL = ""               # label next to the station (e.g. "ISS"); empty string - no label
ISS_SIZE = 1.35              # size of the station icon
ISS_TRAIL = 22               # trail length
ISS_BODY, ISS_BODY_NIGHT = "#f4f6f8", "#8f98a3"      # modules
ISS_TRUSS, ISS_TRUSS_NIGHT = "#c9ced4", "#6c737c"    # truss
ISS_PANEL, ISS_PANEL_NIGHT = "#e2ab3c", "#7d5f22"    # solar arrays
ISS_TRAIL_COLOR = "#ffe7a6"

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

def lerp_color(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


N = NIGHT_STEPS
OCEAN_SHADES = [lerp_color(OCEAN, OCEAN_NIGHT, k / N) for k in range(N + 1)]
LAND_SHADES = [lerp_color(LAND_FILL, LAND_NIGHT, k / N) for k in range(N + 1)]
EDGE_SHADES = [lerp_color(LAND_EDGE, EDGE_NIGHT, k / N) for k in range(N + 1)]
# gradient band edges (pixels): from NIGHT_START to NIGHT_END
BAND_X = [(NIGHT_START + (NIGHT_END - NIGHT_START) * k / N) * RADIUS for k in range(1, N + 1)]
CIRCLE = [(RADIUS * math.cos(2 * math.pi * i / 120), RADIUS * math.sin(2 * math.pi * i / 120))
          for i in range(120)]


def make_ring(radius, a):
    """Atmosphere ring: polygon + shades from day to night (darkening on the night side)."""
    poly = [(radius * math.cos(2 * math.pi * i / 120), radius * math.sin(2 * math.pi * i / 120))
            for i in range(120)]
    day = lerp_color(BG, ATMO_COLOR, a)
    night = lerp_color(BG, ATMO_COLOR, a * ATMO_NIGHT)
    return poly, [lerp_color(day, night, t / N) for t in range(N + 1)]


# from the largest (almost invisible) to the one closest to the surface (brightest)
ATMO = [
    make_ring(RADIUS + ATMO_WIDTH * (ATMO_RINGS - i) / ATMO_RINGS,
              ATMO_STRENGTH * ((i + 1) / ATMO_RINGS) ** 2)
    for i in range(ATMO_RINGS)
]

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
    for lat0, dlon, r in puffs:
        lon0 = center_lon + dlon
        k = max(0.35, math.cos(math.radians(lat0)))
        poly = []
        for v in range(14):
            ang = 2 * math.pi * v / 14
            poly.append((math.radians(lat0 + r * math.sin(ang)),
                         math.radians(lon0 + r * math.cos(ang) * 1.15 / k)))
        built.append((poly, (math.radians(lat0), math.radians(lon0))))
    return {"puffs": built, "min_lon": min(p[1][1] for p in built)}


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
HALO_SHADES = [lerp_color(CLOUD_HALO, CLOUD_HALO_NIGHT, t / N) for t in range(N + 1)]
SHADOW_SHADES = [lerp_color(CLOUD_SHADOW, CLOUD_SHADOW_NIGHT, t / N) for t in range(N + 1)]
BODY_SHADES = [lerp_color(CLOUD_BODY, CLOUD_BODY_NIGHT, t / N) for t in range(N + 1)]


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
                dots.append((math.radians(la), math.radians(lo), size, core, rnd.uniform(0, 2 * math.pi)))
    return dots


CITY_LIGHTS = make_city_lights()
CITY_LEVELS = 10
CITY_SHADES = [lerp_color(LAND_NIGHT, CITY_COLOR, i / CITY_LEVELS) for i in range(CITY_LEVELS + 1)]

# --- Window ---
screen = turtle.Screen()
screen.setup(WIDTH, HEIGHT)
screen.screensize(WIDTH - 40, HEIGHT - 40)  # canvas slightly smaller than the window: (0, 0) stays centred, no scrollbars
screen.bgcolor(BG)
screen.title("Обертовий глобус  —  F або подвійний клік: повний екран, Esc: вийти")
screen.tracer(0)
cv = screen.getcanvas()  # draw directly on the tkinter canvas - faster than turtle
root = cv.winfo_toplevel()
fullscreen = False
last_size = None
last_time = None
MAX_STEPS = 4.0  # after a pause (e.g. dragging the window) the animation never jumps by more than 4 frames


def set_fullscreen(on):
    global fullscreen
    fullscreen = on
    root.attributes("-fullscreen", on)


def toggle_fullscreen(event=None):
    set_fullscreen(not fullscreen)


def exit_fullscreen(event=None):
    if fullscreen:
        set_fullscreen(False)


for key in ("<f>", "<F>", "<F11>", "<Double-Button-1>"):
    root.bind(key, toggle_fullscreen)
root.bind("<Escape>", exit_fullscreen)


def fit_to_window():
    """Fits the canvas to the window size and returns the scale (1 = original size)."""
    global last_size, view_hw, view_hh
    w, h = max(2, cv.winfo_width()), max(2, cv.winfo_height())
    if (w, h) != last_size:
        last_size = (w, h)
        screen.screensize(max(100, w - 40), max(100, h - 40))  # (0, 0) stays centred
    k = min(w, h) / WIDTH
    if abs(k - 1) < 0.05:
        k = 1.0
    view_hw, view_hh = w / 2 / k, h / 2 / k
    return k

angle = 0.0


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


def fill(poly, color):
    if len(poly) >= 3:
        flat = []
        for x, y in poly:
            flat.append(x)
            flat.append(-y)
        cv.create_polygon(flat, fill=color, outline="")


def fill_night(poly, shades):
    """Draws a polygon in its day colour, then darker bands on the left on top (night gradient)."""
    fill(poly, shades[0])
    shape = poly
    drawn = shades[0]
    for k, x_max in enumerate(BAND_X, start=1):
        shape = clip_left(shape, x_max)
        if len(shape) < 3:
            break
        if shades[k] != drawn:  # a band of the same colour as the one below changes nothing - skip it
            fill(shape, shades[k])
            drawn = shades[k]


def night_level(x):
    """0 = day, N = full night (for x in pixels)."""
    f = (NIGHT_START * RADIUS - x) / ((NIGHT_START - NIGHT_END) * RADIUS)
    return max(0, min(N, round(f * N)))


def draw_land(rot):
    """Fill and outlines of the continents on the visible hemisphere."""
    for poly in LAND:
        pts = [project(lat, lon, rot) for lat, lon in poly]
        if all(p[2] < 0 for p in pts):
            continue  # continent is entirely on the far side

        # fill: far-side points are clamped to the edge of the disc
        flat = []
        for x, y, z in pts:
            if z < 0:
                d = math.hypot(x, y) or 1.0
                x, y = x / d * RADIUS, y / d * RADIUS
            flat.append((x, y))
        fill_night(flat, LAND_SHADES)

        # outline: only where both points are on the near hemisphere
        n = len(pts)
        for i in range(n):
            x1, y1, z1 = pts[i]
            x2, y2, z2 = pts[(i + 1) % n]
            if z1 >= 0 and z2 >= 0:
                cv.create_line(x1, -y1, x2, -y2,
                               fill=EDGE_SHADES[night_level((x1 + x2) / 2)], width=1.4)


def draw_stars():
    for x, y, size, color, phase, speed in STARS:
        if abs(x) > view_hw or abs(y) > view_hh:
            continue  # outside the visible area (relevant for fullscreen)
        b = 1 - STAR_TWINKLE * (0.5 + 0.5 * math.sin(tick * speed + phase))  # 1 = brightest, 0 = almost faded out
        r = size * (0.7 + 0.3 * b)  # the star "breathes" slightly along with its brightness
        cv.create_oval(x - r, -y - r, x + r, -y + r,
                       fill=lerp_color(BG, color, 0.06 + 0.94 * b), outline="")


def scaled(pts, mx, my, k, dy):
    return [(mx + (x - mx) * k, my + (y - my) * k + dy) for x, y in pts]


def draw_cities(rot):
    """City lights: glow only on the night side, flicker slightly, hidden by clouds."""
    for lat, lon, size, core, phase in CITY_LIGHTS:
        x, y, z = project(lat, lon, rot)
        if z < 0.08:
            continue  # beyond the horizon or too close to the edge
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
            cv.create_rectangle(x - b * 1.9, -y - b * 1.9, x + b * 1.9, -y + b * 1.9,
                                fill=CITY_SHADES[max(1, idx // 3)], outline="")
        cv.create_rectangle(x - b, -y - b, x + b, -y + b, fill=CITY_SHADES[idx], outline="")


def draw_satellites(front):
    """Satellites with trails. front=False - those behind the Earth (drawn before the globe, so the globe covers them)."""
    for r, u, v, omega, phase in ORBITS:
        direction = 1 if omega > 0 else -1
        theta = phase + omega * tick
        pts = []
        for j in range(SAT_TRAIL + 1):
            t = theta - direction * j * SAT_TRAIL_STEP
            c, sn = math.cos(t), math.sin(t)
            pts.append((r * (c * u[0] + sn * v[0]),
                        r * (c * u[1] + sn * v[1]),
                        r * (c * u[2] + sn * v[2])))

        # trail: segments fade out to the background colour
        for j in range(SAT_TRAIL):
            (x1, y1, z1), (x2, y2, z2) = pts[j], pts[j + 1]
            if ((z1 + z2) >= 0) != front:
                continue
            base = SAT_TRAIL_SHADES[night_level((x1 + x2) / 2)]
            fade = 1.0 * (1 - j / SAT_TRAIL)
            cv.create_line(x1, -y1, x2, -y2, fill=lerp_color(BG, base, fade), width=2)

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
    theta = ISS_PHASE + ISS_SPEED * tick
    pts = []
    for j in range(ISS_TRAIL + 1):
        t = theta - j * SAT_TRAIL_STEP
        c, sn = math.cos(t), math.sin(t)
        pts.append((ISS_R * (c * ISS_U[0] + sn * ISS_V[0]),
                    ISS_R * (c * ISS_U[1] + sn * ISS_V[1]),
                    ISS_R * (c * ISS_U[2] + sn * ISS_V[2])))

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
    k = ISS_SIZE * (0.85 + 0.15 * z / ISS_R)
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


def draw_clouds(rot):
    """Fluffy clouds: soft edge, shadow underneath, white top; they darken at night along with the surface."""
    rot = tick * SPEED * CLOUD_DRIFT  # does not reset after a full revolution
    update_clouds(rot)
    all_puffs = [puff for system in CLOUD_LIST for puff in system["puffs"]]
    limit = RADIUS * CLOUD_SCALE
    puffs = []
    for poly, (clat, clon) in all_puffs:
        cx, cy, cz = project(clat, clon, rot)
        if cz < 0.12:
            continue  # centre is too close to the edge or beyond the horizon
        lvl = night_level(cx * CLOUD_SCALE)
        pts = []
        for lat, lon in poly:
            x, y, z = project(lat, lon, rot)
            x, y = x * CLOUD_SCALE, y * CLOUD_SCALE
            if z < 0:
                d = math.hypot(x, y) or 1.0
                x, y = x / d * limit, y / d * limit
            pts.append((x, y))
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        hy = (max(p[1] for p in pts) - min(p[1] for p in pts)) / 2
        puffs.append((pts, mx, my, hy, min(N, round(lvl * 1.35))))  # clouds darken faster than the surface

    # draw each layer for all puffs together so they merge into a single cloud
    for pts, mx, my, hy, lvl in puffs:
        fill(scaled(pts, mx, my, 1.3, 0), HALO_SHADES[lvl])
    for pts, mx, my, hy, lvl in puffs:
        fill(scaled(pts, mx, my, 1.0, -0.18 * hy), SHADOW_SHADES[lvl])
    for pts, mx, my, hy, lvl in puffs:
        fill(scaled(pts, mx, my, 0.88, 0.14 * hy), BODY_SHADES[lvl])


static_k = None


ATMO_SECTORS = 240  # number of arcs each atmosphere ring is split into


def build_static(k):
    """Draws the layer that does not change between frames (atmosphere and ocean) and tags it "static".

    The atmosphere is thin rings made of arcs (no large filled areas, so Tk draws them quickly);
    the colour of each arc depends on its position relative to the night boundary.
    """
    global static_k
    cv.delete("all")
    thick = ATMO_WIDTH / ATMO_RINGS
    step = 360.0 / ATMO_SECTORS
    for i, (poly, shades) in enumerate(ATMO):
        r_mid = RADIUS + ATMO_WIDTH * (ATMO_RINGS - i - 0.5) / ATMO_RINGS
        rk = r_mid * k
        for j in range(ATMO_SECTORS):
            theta = j * step
            x = r_mid * math.cos(math.radians(theta + step / 2))
            cv.create_arc(-rk, -rk, rk, rk, start=theta, extent=step + 0.8, style="arc",
                          outline=shades[night_level(x)], width=thick * k + 0.8)
    cv.addtag_all("static")
    fill_night(CIRCLE, OCEAN_SHADES)  # ocean
    cv.addtag_all("ocean")
    cv.dtag("static", "ocean")
    if k != 1.0:
        cv.scale("ocean", 0, 0, k, k)
    cv.addtag_withtag("static", "ocean")
    static_k = k


def draw_frame():
    global angle, tick, last_time
    started = time.perf_counter()
    # animation depends on real time, not on the frame count:
    # rotation speed is the same in a window and in fullscreen (where frames take longer to draw)
    steps = 1.0 if last_time is None else min(MAX_STEPS, (started - last_time) * 1000 / FRAME_MS)
    last_time = started
    global static_k
    k = fit_to_window()
    if k != static_k:
        build_static(k)               # static layer (atmosphere and ocean) is drawn once and again on resize
    else:
        cv.delete("dyn")              # the rest of the frame is redrawn every time
    draw_stars()                      # background stars
    draw_satellites(front=False)      # satellites behind the Earth
    draw_iss(front=False)             # ISS when it is behind the Earth
    cv.addtag_all("behind")           # everything behind the Earth is lowered beneath the static layer (atmosphere and ocean)
    cv.dtag("static", "behind")
    cv.tag_lower("behind")
    draw_land(angle)                  # continents
    draw_cities(angle)                # city lights on the night side
    draw_clouds(angle)                # clouds
    draw_satellites(front=True)       # satellites in front of the Earth
    draw_iss(front=True)              # ISS in front of the Earth

    cv.addtag_all("dyn")              # tag everything drawn in this frame
    cv.dtag("static", "dyn")
    if k != 1.0:
        cv.scale("dyn", 0, 0, k, k)   # scale the image together with the window

    angle = (angle + SPEED * steps) % (2 * math.pi)
    tick += steps
    spent = (time.perf_counter() - started) * 1000
    screen.ontimer(draw_frame, max(1, int(FRAME_MS - spent)))  # keep ~40 frames/s if we can keep up


draw_frame()
screen.mainloop()
