"""The background stars."""

import math
import random

from earth import state
from earth.config import ATMO_WIDTH, BG, HEIGHT, RADIUS, STAR_COLORS, STAR_COUNT, STAR_TWINKLE, WIDTH
from earth.state import layer_on
from earth.util import lerp_color
from earth.window import cv


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


star_items = []      # (canvas item, x, y, size, colour, phase, speed) in screen pixels
STAR_UPDATE_EVERY = 6  # twinkling changes slowly, so stars are updated every few frames only
last_star_tick = -100.0


def build_stars(k):
    """Stars are persistent canvas items (created with the static layer) - they cost nothing between updates."""
    global last_star_tick
    star_items.clear()
    last_star_tick = -100.0   # the stars are redrawn at once on the next update
    for x, y, size, color, phase, speed in STARS:
        if abs(x) > state.view_hw or abs(y) > state.view_hh:
            continue  # outside the visible area (relevant for fullscreen)
        item = cv.create_oval((x - size) * k, (-y - size) * k, (x + size) * k, (-y + size) * k,
                              fill=color, outline="", tags=("static", "stars"))
        star_items.append((item, x * k, -y * k, size * k, color, phase, speed))


def update_stars():
    global last_star_tick
    if state.quality >= 1 or not layer_on["stars"]:
        return  # no twinkling on a slow machine (or while the stars are switched off)
    if state.tick - last_star_tick < STAR_UPDATE_EVERY:
        return
    last_star_tick = state.tick
    for item, x, y, size, color, phase, speed in star_items:
        b = 1 - STAR_TWINKLE * (0.5 + 0.5 * math.sin(state.tick * speed + phase))  # 1 = brightest, 0 = almost faded out
        r = size * (0.7 + 0.3 * b)  # the star "breathes" slightly along with its brightness
        cv.coords(item, x - r, y - r, x + r, y + r)
        cv.itemconfigure(item, fill=lerp_color(BG, color, 0.06 + 0.94 * b))
