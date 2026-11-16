"""Settings: every number and colour you may want to change. Edit a value and run the program again."""

import math


# --- Settings ---
WIDTH, HEIGHT = 700, 800
RADIUS = 250
TILT = math.radians(23.5)   # axial tilt of the globe
SPEED = math.radians(0.3)   # rotation angle per animation step (one step = TICK_MS ms)
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
CLOUD_SCALE = 1.012          # clouds sit slightly above the surface
CLOUD_DRIFT = 1.15           # clouds rotate slightly faster than the surface

# --- Stars ---
STAR_COUNT = 98              # number of background stars
STAR_COLORS = ["#ffffff", "#cfe0ff", "#fff1d0"]
STAR_TWINKLE = 1.0           # brightness pulsing depth (0 - no pulsing, 1 - almost fade out)

# --- Satellites ---
SATELLITE_COUNT = 10         # most ordinary satellites that can fly at once (the game adds one per level, up to this)
SATELLITE_SEED = 5           # change the number to get a different set of orbits
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
HUD_CLOSE, HUD_AIM = 2.5, 10   # DST turns green within HUD_CLOSE catch radii; BRG within HUD_AIM degrees of straight ahead
HUD_ALT_NEAR = 2               # ALT is green on the SAME altitude level, amber when the two differ by 1 .. HUD_ALT_NEAR levels, white beyond
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

# --- Frame loop ---
MAX_STEPS = 4.0  # after a pause (e.g. dragging the window) the animation never jumps by more than 4 steps
