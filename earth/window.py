"""The window: turtle screen, tkinter canvas, fast drawing helpers and fullscreen.

Importing this module opens the window."""

import turtle

from earth import state
from earth.config import BG, HEIGHT, WIDTH


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


def set_fullscreen(on):
    state.fullscreen = on
    root.attributes("-fullscreen", on)


def toggle_fullscreen(event=None):
    set_fullscreen(not state.fullscreen)


def exit_fullscreen(event=None):
    if state.fullscreen:
        set_fullscreen(False)
