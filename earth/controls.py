"""Keyboard and mouse: one key press is one step; shortcuts are bound in bind_keys()."""

from earth.state import layer_on
from earth.window import cv, exit_fullscreen, root, toggle_fullscreen
from earth.game import climb_player, keys_held, turn_player
from earth.panel import toggle_panel


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


def bind_keys():
    """Binds every keyboard and mouse shortcut of the program."""
    for key in ("<f>", "<F>", "<F11>"):
        root.bind(key, toggle_fullscreen)
    cv.bind("<Double-Button-1>", toggle_fullscreen, add="+")  # on the canvas only: a fast double click on a checkbox must not toggle fullscreen
    root.bind("<Escape>", exit_fullscreen)
    root.bind("<KeyPress>", on_key_press)
    root.bind("<KeyRelease>", on_key_release)
    root.bind("<FocusOut>", lambda e: keys_held.clear())  # never leave a key "stuck" when the window loses focus
    for key in ("<h>", "<H>"):
        root.bind(key, toggle_panel)
