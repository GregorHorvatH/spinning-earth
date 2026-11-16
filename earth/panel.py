"""The control panel: FPS, layer checkboxes, the auto-quality checkbox and the HUD legend."""

import math
import time
import tkinter

from earth import state
from earth.config import (
    CATCH_RADIUS, HEIGHT, HUD_AIM, HUD_ALT_NEAR, HUD_CLOSE, LAYERS, PLAYER_COLOR, PLAYER_TURN_STEP, SHOW_PANEL, WIDTH,
)
from earth.state import layer_on, recent
from earth.window import cv, root, screen
from earth.layout import HUD_AMBER, HUD_DIM, HUD_TEXT
from earth.scene import apply_visibility


PANEL_BG, PANEL_FG = "#0d141c", "#dbe4ee"
GRAPHICS_NAMES = ["full", "reduced", "low", "minimal"]
layer_vars = {}
panel_visible = SHOW_PANEL
fps_frames, fps_since = 0, time.perf_counter()
panel_width = 0


def on_layer_toggle(key):
    layer_on[key] = bool(layer_vars[key].get())
    if key == "night":
        state.static_k = None  # night changes the atmosphere dimming and the full-night line: rebuild the static layers
    else:
        apply_visibility()


def on_auto_toggle():
    state.auto_quality = bool(auto_var.get())
    recent.clear()
    state.quality_wait = 60
    if not state.auto_quality and state.quality:
        state.quality = 0  # switched off by the user = full graphics again: restore everything that was dropped
        apply_visibility()


def resize_window_by(dx):
    """Grows / shrinks the window by dx pixels (not in fullscreen), so the globe area keeps its size."""
    if not state.fullscreen:
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
    ("ALT", HUD_TEXT, "altitude; green = same, amber = 1-%d off" % HUD_ALT_NEAR),
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
    auto_var = tkinter.BooleanVar(master=root, value=state.auto_quality)
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
            graphics_label.config(text="Graphics: " + GRAPHICS_NAMES[state.quality] + (" (auto)" if state.quality else ""))
        fps_frames, fps_since = 0, now
