"""The table of instruments in the top-right corner."""

import math

from earth import state
from earth.config import (
    CATCH_RADIUS, HUD_AIM, HUD_ALT_NEAR, HUD_CLOSE, HUD_MARGIN, PLAYER_ALT_STEP, PLAYER_COLOR, RADIUS, TICK_MS,
)
from earth.state import view_box
from earth.util import dist
from earth.window import cv
from earth.layout import HUD_AMBER, HUD_COLUMNS, HUD_DIM, HUD_GREEN, HUD_LABEL_WIDTH, hud_metrics, HUD_TEXT
from earth.game import (
    active_satellites, intercept_forecast, iss, iss_bearing, iss_pos, level, player, player_pos, turtle_speed,
)


def draw_hud():
    """Top-right panel: score, level and a table of instruments. Drawn in screen pixels, after the globe has been
    scaled and shifted, so the plate stays put while the globe is centred below it.

    Rows: the ISS and the turtle (TUR). Columns:
      ALT  altitude, Earth radii (green on both on the same level, amber when 1-2 levels apart, white beyond)
      SPD  orbital speed, degrees per second
      DST  distance turtle - ISS, px (green when it is within 2.5 catch radii)
      BRG  where the ISS is relative to your heading: L = left, R = right, in degrees (green when almost ahead)
      ETA  seconds until the closest approach if you press nothing, MIS = the distance then, px.
           MIS below the catch radius (green) means you are on a collision course and will catch it."""
    pl = player
    k = state.static_k or 1.0
    iss_alt = iss["r"] / RADIUS
    eta, miss = intercept_forecast()
    bearing = iss_bearing()
    dst = dist(iss_pos(), player_pos())
    per_s = 1000.0 / TICK_MS
    levels_off = round(abs(pl["alt"] - iss_alt) / PLAYER_ALT_STEP)   # altitude levels between the two
    course = HUD_GREEN if miss < CATCH_RADIUS else (HUD_AMBER if miss < 2 * CATCH_RADIUS else HUD_TEXT)
    if abs(bearing) < 0.5:
        brg = "0\u00b0"
    else:
        brg = "%s%d\u00b0" % ("L" if bearing > 0 else "R", round(abs(bearing)))
    alt_color = HUD_GREEN if levels_off == 0 else (HUD_AMBER if levels_off <= HUD_ALT_NEAR else HUD_TEXT)
    rows = (
        ("ISS", HUD_AMBER, [
            ("%.2f" % iss_alt, alt_color),
            ("%.1f" % math.degrees(iss["omega"] * per_s), HUD_TEXT),
            ("%d" % round(dst), HUD_GREEN if dst < HUD_CLOSE * CATCH_RADIUS else HUD_TEXT),
            (brg, HUD_GREEN if abs(bearing) < HUD_AIM else HUD_TEXT),
            ("--" if eta is None else "%.1fs" % eta, HUD_DIM if eta is None else course),
            ("%d" % round(miss), course)]),
        ("TUR", PLAYER_COLOR, [
            ("%.2f" % pl["alt"], alt_color),
            ("%.1f" % math.degrees(turtle_speed(pl["alt"]) * per_s), HUD_TEXT),
            ("-", HUD_DIM), ("-", HUD_DIM), ("-", HUD_DIM), ("-", HUD_DIM)]),
    )

    table_font, cw, lh, title_font, tcw, tlh, pad, row_h, plate_h = hud_metrics(k)
    title = "SCORE: %04d" % state.score
    info = "LVL %02d   SAT %02d" % (level(), active_satellites())
    table_w = (HUD_LABEL_WIDTH + sum(w for _, w in HUD_COLUMNS)) * cw
    plate_w = max(table_w, len(title) * tcw) + 2 * pad
    left, top, right, bottom = view_box              # the real visible edges of the canvas, in screen pixels
    x1, y0 = right - HUD_MARGIN, top + HUD_MARGIN    # the plate is the same distance from the right and the top edge
    x0, y1 = x1 - plate_w, y0 + plate_h

    cv.create_rectangle(x0, y0, x1, y1, fill="#0a1017", outline="#26323f")
    tx, ty = x0 + pad, y0 + pad
    cv.create_text(tx, ty, text=title, anchor="nw", fill=HUD_GREEN, font=title_font)
    ty += tlh
    cv.create_text(tx, ty, text=info, anchor="nw", fill=HUD_DIM, font=table_font)
    ty += round(lh * 1.3)
    right_edge = [tx + (HUD_LABEL_WIDTH + sum(w for _, w in HUD_COLUMNS[:j]) + w - 1) * cw
                  for j, (_, w) in enumerate(HUD_COLUMNS)]   # right edge of each column (one character is the gap)
    for (name, _), x in zip(HUD_COLUMNS, right_edge):
        cv.create_text(x, ty, text=name, anchor="ne", fill=HUD_DIM, font=table_font)
    ty += row_h
    for label, label_color, cells in rows:
        cv.create_text(tx, ty, text=label, anchor="nw", fill=label_color, font=table_font)
        for (text, color), x in zip(cells, right_edge):
            cv.create_text(x, ty, text=text, anchor="ne", fill=color, font=table_font)
        ty += row_h
