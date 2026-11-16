"""State shared between modules: what changes while the program runs.

A value that is REBOUND (`quality = ...`) must live here and be used as `state.quality`: a name imported with
`from earth.state import quality` would be a stale copy. Objects that are only changed in place (the `layer_on`
dict, the `recent` list, ...) can be imported by name."""

from earth.config import AUTO_QUALITY, HEIGHT, LAYERS, NIGHT_END, RADIUS, WIDTH


# --- layers ---
layer_on = {key: True for key, _ in LAYERS}  # current state of the checkboxes (cached, so frames never ask Tk)

# --- time ---
tick = 0            # animation time in steps (one step = TICK_MS ms)
angle = 0.0         # how far the globe has turned (radians)
last_time = None    # when the previous frame started (time.perf_counter); None before the first frame

# --- the window and the static layer ---
view_hw, view_hh = WIDTH / 2, HEIGHT / 2  # visible area in "world" coordinates
view_box = [-WIDTH / 2, -HEIGHT / 2, WIDTH / 2, HEIGHT / 2]  # the same area in screen pixels: left, top, right, bottom
fullscreen = False
static_k = None   # scale the static layer was built for (None = not built yet)
static_dy = None  # ... and how far below the canvas centre it put the globe (screen pixels)
static_imgs = []  # keeps the PhotoImage objects alive
XE = NIGHT_END * RADIUS  # left of this x it is full night (objects use plain dark colours there)

# --- quality ---
quality = 0        # 0 = everything ... 3 = minimal (only ever goes down; resets when the window size changes)
quality_wait = 60  # frames to wait (start-up, or after a change) before judging again
recent = []        # real intervals (ms) between the last frames
auto_quality = AUTO_QUALITY  # the "Auto-reduce graphics" switch while the program runs (AUTO_QUALITY is only its start value)

# --- the game ---
score = 0
