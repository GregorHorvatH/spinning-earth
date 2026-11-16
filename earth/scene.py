"""The parts of the picture that do not change between frames, which layers are visible, and the automatic quality."""

import base64
import math
import tkinter

from earth import state
from earth.config import NIGHT_END, OCEAN, QUALITY_MIN_FPS, QUALITY_WINDOW, RADIUS
from earth.state import layer_on, recent
from earth.night import OCEAN_DARK
from earth.window import cv, root
from earth.geometry import clip_left
from earth.stars import build_stars
from earth.images import make_atmo_tiles, make_night_strip


def build_static(k, dy=0):
    """Builds the layers that do not change between frames and tags them "static":
    atmosphere tiles, the ocean (a plain oval + its dark part) and the narrow night-gradient strip.
    dy = how many screen pixels below the canvas centre the globe's centre is put (see globe_shift)."""
    # the "full night" line is exactly where the gradient strip begins, so land, clouds and the dark ocean all
    # switch to night colours on the same pixel column; with the night layer off there is no such line at all
    state.XE = math.ceil(NIGHT_END * RADIUS * k) / k if layer_on["night"] else -1e9
    cv.delete("all")
    state.static_imgs = []
    build_stars(k)  # stars go first = they are at the very bottom
    for x0, y0, png in make_atmo_tiles(k):
        img = tkinter.PhotoImage(master=root, data=base64.b64encode(png))
        state.static_imgs.append(img)
        cv.create_image(x0, y0 + dy, image=img, anchor="nw", tags=("static", "atmo"))
    r = RADIUS * k
    cv.create_oval(-r, -r + dy, r, r + dy, fill=OCEAN, outline="", tags=("static", "ocean"))
    circle = [(RADIUS * math.cos(2 * math.pi * i / 360), RADIUS * math.sin(2 * math.pi * i / 360)) for i in range(360)]
    x0, top, width, height, png = make_night_strip(k)
    if layer_on["night"]:
        dark = clip_left(circle, state.XE)
        cv.create_polygon([c for p in dark for c in (p[0] * k, -p[1] * k + dy)], fill=OCEAN_DARK, outline="",
                          tags=("static", "ocean"))
    img = tkinter.PhotoImage(master=root, data=base64.b64encode(png))
    state.static_imgs.append(img)
    cv.create_image(x0, -top + dy, image=img, anchor="nw", tags=("static", "shade"))
    state.static_k, state.static_dy = k, dy


def apply_visibility():
    """Shows or hides the persistent canvas items: a layer is visible if its checkbox is ticked AND the
    automatic quality level has not dropped it.
    Quality level 1: no cloud halo, no star twinkle. 2: half the clouds, no satellite trails, only the main city
    lights, no atmosphere glow. 3: no clouds, no city lights, no stars."""
    def shown(on):
        return "normal" if on else "hidden"
    cv.itemconfigure("stars", state=shown(layer_on["stars"] and state.quality < 3))
    cv.itemconfigure("atmo", state=shown(layer_on["atmo"] and state.quality < 2))
    cv.itemconfigure("ocean", state=shown(layer_on["ocean"]))
    cv.itemconfigure("shade", state=shown(layer_on["night"]))


def adapt_quality(interval_ms):
    """Watches the real frame intervals and, if the machine cannot keep up, lowers the quality one level.
    It uses the median of the last QUALITY_WINDOW frames: a one-off stall (window drag, a system hiccup,
    the slow first frames) cannot trigger it, only a consistently low frame rate can."""
    if not state.auto_quality or state.quality >= 3:
        return
    recent.append(interval_ms)
    if len(recent) > QUALITY_WINDOW:
        del recent[0]
    state.quality_wait -= 1
    if state.quality_wait <= 0 and len(recent) >= QUALITY_WINDOW \
            and sorted(recent)[len(recent) // 2] > 1000.0 / QUALITY_MIN_FPS:
        state.quality += 1
        state.quality_wait = QUALITY_WINDOW
        recent.clear()
        apply_visibility()
