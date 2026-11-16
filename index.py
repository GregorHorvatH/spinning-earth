"""Spinning Earth: an animated globe with a small game on top. Run this file: python3 index.py"""

import math
import time

from earth import state
from earth.config import CLOUD_DRIFT, MAX_STEPS, SPEED, TARGET_FPS, TICK_MS
from earth.state import layer_on, recent
from earth.window import cv, screen
from earth.layout import fit_to_window, globe_shift
from earth.land import draw_land
from earth.clouds import draw_clouds, update_clouds
from earth.stars import update_stars
from earth.scene import adapt_quality, apply_visibility, build_static
from earth.cities import draw_cities
from earth.game import iss, update_game, wrecks
from earth.controls import bind_keys
from earth.sprites import draw_burning, draw_game_overlay, draw_iss, draw_satellites, draw_turtle
from earth.hud import draw_hud
from earth.panel import build_panel, update_fps


def draw_frame():
    started = time.perf_counter()
    update_fps(started)
    if state.last_time is not None and started - state.last_time < 0.5:
        adapt_quality((started - state.last_time) * 1000)
    # animation depends on real time, not on the frame count:
    # rotation speed is the same in a window and in fullscreen (where frames take longer to draw)
    steps = 1.0 if state.last_time is None else min(MAX_STEPS, (started - state.last_time) * 1000 / TICK_MS)
    state.last_time = started
    k = fit_to_window()
    dy = globe_shift(k)               # the globe is centred between the HUD and the bottom of the window
    if k != state.static_k or dy != state.static_dy:
        if state.static_k is not None and k != state.static_k:  # window size changed: judge the quality again from scratch
            state.quality, state.quality_wait = 0, 60
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
        draw_land(state.angle)        # continents
    if layer_on["clouds"]:
        draw_clouds(state.angle)      # clouds
    else:
        update_clouds(state.tick * SPEED * CLOUD_DRIFT)  # keep the cloud systems moving so they are in place when switched on
    cv.tag_raise("shade")             # night shade over the land and clouds (city lights, satellites go above it)
    if layer_on["cities"] and layer_on["night"]:
        draw_cities(state.angle)      # city lights on the night side
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

    state.angle = (state.angle + SPEED * steps) % (2 * math.pi)
    state.tick += steps
    spent = (time.perf_counter() - started) * 1000
    screen.ontimer(draw_frame, max(1, int(1000 / TARGET_FPS - spent)))  # aim for TARGET_FPS if we can keep up


def setup():
    """Everything except the frame loop itself: the key bindings and the control panel."""
    bind_keys()
    build_panel()


def main():
    setup()
    draw_frame()
    screen.mainloop()


if __name__ == "__main__":
    main()
