"""Where the globe and the HUD go in the window: scale, shift and the HUD size."""

import tkinter
import tkinter.font

from earth import state
from earth.config import ATMO_WIDTH, GLOBE_GAP, HUD_MARGIN, RADIUS, WIDTH
from earth.state import layer_on, view_box
from earth.window import cv, root, screen


last_size = None


def fit_to_window():
    """Fits the canvas to the window size and returns the scale (1 = original size)."""
    global last_size
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
    state.view_hw, state.view_hh = w / 2 / k, h / 2 / k
    return k


HUD_COLUMNS = (("ALT", 6), ("SPD", 6), ("DST", 6), ("BRG", 6), ("ETA", 6), ("MIS", 5))  # (header, width in characters)
HUD_LABEL_WIDTH = 4
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
