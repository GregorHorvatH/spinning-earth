# Spinning Earth

An animated, rotating globe in pure Python: green continents on a blue ocean, a day/night terminator, city lights, clouds, an atmosphere, satellites and the ISS against a starry sky - with a small game on top: fly a turtle around the Earth and catch the space station. No third-party libraries - only the Python standard library.

![Screenshot](docs/screenshot.png)

## Features

- **Day and night** - the left hemisphere is in darkness, with a smooth gradient across the middle.
- **City lights** on the night side (132 major cities, each surrounded by smaller lights). They switch off as a city approaches the daylight.
- **Clouds** - fluffy, with a shadow underneath. They are destroyed past the right horizon and created behind the left one, so there is no visible repeat after a full revolution. They darken at night.
- **Atmosphere** - a translucent glow around the globe that fades out on the night side.
- **10 satellites** on different orbits with trails, and the **ISS** on an orbit with its real 51.6° inclination. (In the game the satellites appear one per level; with the game switched off all 10 fly.)
- **Stars** that pulse slowly.
- **Fullscreen** - the picture scales together with the window.
- The animation is driven by real time, so the speed is the same in a window and in fullscreen, and on a fast or a slow computer.
- **A small game** - fly a turtle around the Earth and catch the ISS. Every catch makes the station burn up in the atmosphere, raises the level (a faster ISS and one more satellite) and the score in the top-right corner; a table of instruments (altitude, speed, distance, bearing, time and distance of the closest pass) helps you plan the interception (see [Game](#game)).
- **Control panel** - a live FPS counter and a checkbox for every layer, so you can switch layers on and off yourself (see [Control panel](#control-panel)).
- **Automatic quality** - on a slow machine the program drops detail step by step until the animation runs smoothly. It can be switched off with a checkbox (see [Performance](#performance)).

## Requirements

- **Python 3** with **tkinter** support (`turtle` runs on top of it).
- No packages from PyPI are needed: there is no `pip install` step and no `requirements.txt`. The code only imports standard-library modules (`math`, `random`, `time`, `struct`, `zlib`, `base64`, `turtle`, `tkinter`).

Tested on Python 3.14 (Tk 9.0) on macOS. The code does not use anything specific to recent Python versions, but it has not been run on older ones.

### Check that tkinter is available

```bash
python3 -m tkinter
```

A small "tkinter" window should open. If you get `No module named '_tkinter'` (or `tkinter`) instead, install it using the instructions for your system below.

### Installing tkinter

| System | Command |
|---|---|
| **macOS** (Python from [python.org](https://www.python.org/downloads/)) | Nothing to do - tkinter is bundled. |
| **macOS** (Homebrew) | `brew install python-tk` (or `python-tk@3.13` - use your Python version) |
| **Ubuntu / Debian** | `sudo apt install python3-tk` |
| **Fedora** | `sudo dnf install python3-tkinter` |
| **Arch Linux** | `sudo pacman -S tk` |
| **Windows** | Nothing to do if you installed Python from [python.org](https://www.python.org/downloads/). Make sure *tcl/tk and IDLE* was ticked during installation. |

On macOS, avoid the Python that ships with the system: it uses an outdated Tk that runs unreliably. Prefer Python from python.org or Homebrew.

## Running

```bash
cd globe
python3 index.py
```

On Windows use `python` or `py` instead of `python3`.

### Standalone app (optional)

The program can be packed into an application that runs without Python installed, with [PyInstaller](https://pyinstaller.org):

```bash
pip install pyinstaller
pyinstaller --windowed --name "Spinning Earth" index.py
```

The result is `dist/Spinning Earth.app` (about 31 MB: Python and Tk are inside). Notes:

- The program is `index.py` plus the `earth/` folder; PyInstaller finds all the modules by itself, there is nothing extra to configure.
- Tested on macOS with Apple Silicon: the app starts and runs from an environment with nothing but `/usr/bin:/bin` on the `PATH`. PyInstaller builds for the machine it runs on and cannot cross-compile, so for Windows or Linux run the command on that system (not tried).
- The app is only ad-hoc signed, not notarised. On another Mac the first launch may need a right click, then **Open**; this has not been tried on another Mac.
- The build leaves `build/`, `dist/` and a `.spec` file next to the code: keep them out of version control.

## Controls

| Action | Result |
|---|---|
| `F` or `F11` | toggle fullscreen |
| double-click the globe | same |
| `H` | hide / show the control panel |
| `←` `→` | game: turn the turtle's orbit left / right (one 15 degree step per press) |
| `↑` `↓` | game: raise / lower the turtle's orbit (one altitude level per press) |
| `Esc` | leave fullscreen |
| close the window | quit |

The scale follows the smaller side of the window, so on wide screens the globe simply gets more space around it.

## Game

Fly the turtle around the Earth and **catch the ISS**. Every catch adds 1 to the score (top-right corner, `SCORE: 0000`), the station reappears on a new random orbit, and the game gets harder (see [Levels](#levels)).

| Key | What it does |
|---|---|
| `←` / `→` | turn the turtle's orbit left / right by **15 degrees** |
| `↑` / `↓` | raise / lower the orbit by **one altitude level** (7 levels, 1.10 to 1.34 Earth radii) |

**One press is one step.** Holding a key does nothing more (the keyboard's auto-repeat is ignored), so a value never runs away from you: tap again for the next step. The window title and the panel remind you of this.

How it works:

- The turtle is always in orbit; you steer, you never stop. `←` / `→` rotate the direction of flight around the radial axis through the turtle, which tilts the orbital plane (a plane-change manoeuvre).
- `↑` / `↓` change the altitude. Lower orbits are faster and higher ones slower (Kepler: speed grows as altitude drops), so altitude is also your throttle for catching up with the station or waiting for it.
- A dotted green line shows where the current orbit leads, so you can see what each tap will do; a solid green line is the trail behind you. When the turtle is behind the Earth it is hidden, and a dim outline is drawn on top so you do not lose it. On the night side the turtle fades to dark green, almost black, like everything else, and so does the solid trail behind it (it darkens gradually where it crosses the day / night line). The dotted line ahead of the turtle stays bright on purpose: it is the planning aid that shows what each key press will do.
- The ISS has a dashed ring, which is the catch zone; it turns green when you are close. The ISS always appears on one of the same 7 altitude levels, so the altitudes can be matched exactly (see [the instruments](#the-instruments)).
- **A caught station falls and burns up,** in two short, simple steps (under a second in all). First it **falls**, intact, turning orange and faster and faster, until it reaches the top of the air. Then it **burns** inside a single fireball that swells and shrinks while the station melts away, and it ends with a flash. Falling from a higher orbit takes a little longer. The next station is already flying on its new orbit meanwhile, so the game never waits. On the night side the fireball is bright against the dark; behind the Earth it is hidden by the globe, like everything else there.
- Ordinary satellites are obstacles. A collision knocks the turtle slightly off its orbit: the flight direction turns about 12-22 degrees away from the satellite and the altitude shifts by one level. The turtle tumbles and blinks for a moment, and cannot be hit again for about a second.
- The whole game can be switched off with the **Game** checkbox (the ISS then just flies its orbit).

### Levels

The level is the number of caught stations plus one, and it is shown in the HUD (`LVL 05   SAT 04`).

- **Level 1:** no ordinary satellites at all, only the ISS, and it hardly moves (about 2 degrees per second against the turtle's 46).
- **Every next level adds one satellite** (up to `SATELLITE_COUNT`, 10, reached on level 11) **and makes the ISS faster.** A new satellite appears on its own orbit, never right on top of the turtle, and a blue ring marks where it showed up.
- **The ISS speed is a fraction of the turtle's own speed on the ISS's orbit,** so it can never overtake the turtle. It starts at 5% and grows in shrinking steps: +0.20, +0.14, +0.10, +0.07, and from then on +0.05 per level until it stops at 95% of the turtle's speed (level 13). The first levels get harder quickly, the later ones slowly.

| Level | Satellites | ISS speed, % of the turtle's | ISS speed, degrees / s |
|---|---|---|---|
| 1 | 0 | 5% | 2 |
| 2 | 1 | 25% | 11 |
| 3 | 2 | 39% | 18 |
| 4 | 3 | 49% | 22 |
| 5 | 4 | 56% | 26 |
| 6 | 5 | 61% | 28 |
| 8 | 7 | 71% | 32 |
| 11 | 10 | 86% | 39 |
| 12 | 10 | 91% | 42 |
| 13 | 10 | 95% | 44 |

(The degrees per second are for an orbit at altitude 1.22; the turtle does 46 there. A lower orbit is faster for both of them.)

Everything above is set by `ISS_SPEED_START`, `ISS_SPEED_FIRST_STEP`, `ISS_SPEED_DECAY`, `ISS_SPEED_MIN_STEP`, `ISS_SPEED_MAX` and `SATELLITE_COUNT` in [earth/config.py](earth/config.py).

### The instruments

The HUD in the top-right corner is a table of instruments, so you can plan an interception instead of guessing. The ISS row is `ISS`, the turtle row is `TUR`:

```
SCORE: 0004
LVL 05   SAT 04
        ALT    SPD    DST    BRG    ETA    MIS
ISS    1.18   26.8    227  R173°  14.7s    162
TUR    1.22   45.8      -      -      -      -
```

| Column | Meaning |
|---|---|
| `ALT` | altitude of the ISS and of the turtle, in Earth radii. **Green on both** only when they are on the **same level**, **amber** when they differ by 1 or 2 levels, white when they are further apart. One level is about 10 px, so two levels apart is 20 px of the 30 px catch zone: you can still catch the station, but only with a more exact position. |
| `SPD` | orbital speed, degrees per second. |
| `DST` | distance from the turtle to the ISS, in pixels (the catch zone is `CATCH_RADIUS` = 30). Green when it is within 2.5 catch radii. |
| `BRG` | where the ISS is relative to the turtle's heading: `L` = to the left, `R` = to the right, in degrees (`0°` = dead ahead, `180°` = behind). Green when it is within 10 degrees of straight ahead. |
| `ETA` | **seconds until the closest approach if you press nothing.** If that approach would catch the ISS, it is the **first** such pass (the station disappears when caught, so a later lap does not matter). `--` means the two only move apart. |
| `MIS` | **how close they will be at that moment, in pixels.** Green when it is below the catch radius (you are on a collision course and will catch it), amber below twice that (a near miss), white otherwise. |

`ETA` and `MIS` come from a forecast that lets both objects keep flying their current orbits for the next 15 seconds (`FORECAST_SECONDS`) and finds the closest pass (or the first pass that gets inside the catch zone). It is exact for what the game itself will do (checked against a step-by-step simulation: the time within half a step, the distance within a third of a pixel), so every key press changes the numbers at once and you can see what a tap would do before you commit to it. A typical interception: match the altitude with `↑` / `↓` until `ALT` is green, turn with `←` / `→` until `MIS` goes green, then wait for `ETA`.

Ordinary satellites are not in the table: the forecast covers the station only.

The same explanations are always on screen: the **HUD (top right)** section of the side panel lists every value of the table, in the same colours, with the thresholds at which it turns green or amber. Those numbers are taken from the constants the HUD itself uses (`CATCH_RADIUS`, `HUD_CLOSE`, `HUD_AIM`, `HUD_ALT_NEAR`), so the text cannot drift away from the game. Hide the panel with `H` when you no longer need it.

### Window and layout

The window is 700 x 800 (`WIDTH`, `HEIGHT`); the extra height makes room for the HUD. The globe is centred **between the bottom of the HUD and the bottom edge of the window,** not between the top and the bottom edge, and it is scaled so that it, with its glow, always fits there with at least `GLOBE_GAP` free pixels on both sides, in a window of any size and in fullscreen. The HUD itself keeps its size in fullscreen and in big windows (it does not grow with the picture); only in a window smaller than the standard one it shrinks, so that it does not cover the whole globe. With the Game layer switched off there is no HUD and the globe is simply centred.

### How hard is it really?

In automated play (a scripted pilot that presses one key every 0.25 s) the game never got stuck: the pilot kept catching the station for 25 minutes of game time and reached levels 66 to 79. A catch took 1 to 8 s on average on levels 1 to 11 and about 24 s on levels 12 and up (14 to 36 s depending on the level), and the slowest single catch took 70 s. A slower pilot (one key every 0.4 s) reached levels 57 to 61: 4 to 17 s per catch on average early on and about 29 s on levels 12 and up (the slowest single catch took 64 s). The scripted pilot only reacts to the current situation; it does not use the `ETA` / `MIS` instruments. Nobody has played it by hand yet, so the real difficulty is untested; if it is too easy or too hard, the constants above are the place to change it.

## Control panel

The panel on the left shows the current **FPS** and the **graphics level** (`full`, or `reduced` / `low` / `minimal (auto)` if the automatic quality reduction has kicked in). Below it is one checkbox per layer:

| Checkbox | Layer |
|---|---|
| Stars | background stars |
| Atmosphere | the glow around the globe |
| Ocean | the ocean disc |
| Continents | land and coastlines |
| Day / night | the night side and the gradient between day and night |
| City lights | lights on the night side |
| Clouds | clouds |
| Satellites | the satellites and their trails |
| ISS | the space station |
| Game (turtle, score) | the turtle, the target ring on the ISS, the HUD table, the score and the burning of caught stations. Switched off, the ISS just flies its orbit and all 10 satellites fly. The ISS itself is the ISS checkbox |

A ticked box means the layer is shown; an unticked one hides it completely (and a hidden layer costs nothing to draw, so switching layers off also raises the frame rate).

- **Day / night** off means the whole globe is lit evenly and the atmosphere is not dimmed. City lights only exist at night, so they disappear too.
- **Auto-reduce graphics** is the automatic quality reduction for slow computers (see [Performance](#performance)). Untick it and the graphics will never be degraded automatically; if it had already degraded them, they are restored to full at once.
- The panel is a column next to the picture, not an overlay: native widgets on top of a canvas that is redrawn every frame make macOS recompose them constantly, which cost about 25 FPS in testing. Hiding it with `H` shrinks the window back by the panel's width.
- Set `SHOW_PANEL = False` in [earth/config.py](earth/config.py) to start with the panel hidden.

## Configuration

All settings are constants in [earth/config.py](earth/config.py), each with a comment; the map data (`CONTINENTS` and `CITIES`) is in [earth/data.py](earth/data.py). Change a value in the file and run the program again (the values are read when the program starts, not while it runs).

| Constant | What it changes |
|---|---|
| `WIDTH`, `HEIGHT`, `RADIUS` | size of the globe area (the window is 700 x 800 by default) and of the globe |
| `SPEED` | rotation speed (degrees per animation step; one step = `TICK_MS` ms) |
| `TARGET_FPS` | frame rate to aim for (the speed of motion does not depend on it) |
| `SHOW_PANEL` | whether the control panel is visible at start |
| `AUTO_QUALITY`, `QUALITY_MIN_FPS`, `QUALITY_WINDOW` | automatic quality reduction on slow machines, the frame rate below which it kicks in, and how many recent frames it looks at |
| `TILT` | tilt of the Earth's axis |
| `OCEAN`, `LAND_FILL`, `LAND_EDGE` | ocean and land colours |
| `NIGHT_START`, `NIGHT_END`, `NIGHT_DARKNESS` | where the day-to-night transition starts and ends, and how dark the night side gets |
| `ATMO_COLOR`, `ATMO_WIDTH`, `ATMO_STRENGTH` | colour, thickness and brightness of the atmosphere |
| `CLOUD_SYSTEMS` | number of cloud clusters |
| `STAR_COUNT`, `STAR_TWINKLE` | number of stars and the depth of their pulsing |
| `SATELLITE_COUNT`, `SATELLITE_SEED` | number of satellites and which set of orbits they get |
| `ISS_SIZE`, `ISS_INCLINATION`, `ISS_LABEL` | ISS icon size, orbit inclination and the label next to it (empty = no label) |
| `CATCH_RADIUS`, `PLAYER_SPEED`, `PLAYER_TURN_STEP`, `PLAYER_ALT_STEP`, `PLAYER_ALT_RANGE`, `PLAYER_SIZE`, `PLAYER_COLOR*`, `PLAYER_EDGE*`, `PLAYER_TRAIL*`, `HUD_MARGIN` | the size of the catch zone, how far one key press turns / raises the orbit, how the turtle flies, and how far the score sits from the top / right edge |
| `BUMP_RADIUS`, `BUMP_TURN`, `BUMP_LEVELS`, `BUMP_COOLDOWN` | how satellite collisions knock the turtle off course |
| `ISS_ALT_RANGE` | the altitudes a newly spawned ISS can appear at |
| `BURN_ANIMATION` | `False` makes a caught station simply disappear |
| `BURN_FALL`, `BURN_FALL_MIN`, `BURN_FIRE` | how long the caught station falls (from the highest / the lowest orbit) and how long it burns, in seconds |
| `BURN_DRIFT`, `BURN_END` | how far it drifts sideways while falling, and how close to the ground it ends |
| `ISS_SPEED_START`, `ISS_SPEED_FIRST_STEP`, `ISS_SPEED_DECAY`, `ISS_SPEED_MIN_STEP`, `ISS_SPEED_MAX` | the difficulty curve: how much faster the ISS gets with every level |
| `FORECAST_SECONDS` | how far ahead the `ETA` and `MIS` instruments look |
| `HUD_CLOSE`, `HUD_AIM`, `HUD_ALT_NEAR` | where `DST` (in catch radii) and `BRG` (in degrees) turn green, and how many levels apart `ALT` stays amber instead of white; the side-panel legend follows them |
| `GLOBE_GAP` | minimum free space between the globe and the HUD above it and the window edge below it |
| `CITY_COLOR`, `CITY_DOTS`, `CITY_VISIBLE_FROM` | colour of the lights, number of smaller lights and how early they switch off |
| `CITIES` (in `earth/data.py`) | list of cities as `(latitude, longitude)` pairs - add your own |
| `CONTINENTS` (in `earth/data.py`) | simplified outlines of continents and islands |
| other colours and sizes | many more are constants in [earth/config.py](earth/config.py), each with a comment: the cloud (`CLOUD_*`), satellite (`SAT_*`) and ISS (`ISS_*`) colours, `PLAYER_REF_ALT` (the turtle's start altitude), `ISS_ORBIT` (the first station's altitude), `NIGHT_STEPS` and so on |

## How it works

(Where each part of this lives in the code: see [Layout](#layout).)

- The continents are a set of simplified polygons with `(longitude, latitude)` coordinates. They are projected onto a sphere, rotated and drawn on a tkinter canvas.
- **Night.** Objects on the night side are drawn in plain dark colours. The smooth day-to-night gradient is one narrow semi-transparent black image laid over the globe, so the ocean, land and clouds all darken together without stacking dozens of clipped polygons.
- **Static layers.** The atmosphere glow and the ocean are rendered once (as small RGBA images, built in pure Python and encoded as PNG, so no imaging library is needed) and rebuilt only when the window is resized. The stars are persistent canvas items that are only re-coloured now and then.
- **Per frame** only the moving things are redrawn: continents, clouds, city lights, satellites, the ISS, the turtle and a burning wreck. Their trigonometry is precomputed and canvas items are created through direct Tcl calls, which is noticeably cheaper than going through tkinter's option parsing.
- **The game** keeps its own state in 3D: the turtle is a point on a sphere with a direction of flight, and the ISS is an orbit in a plane. A key press only turns the direction or changes the altitude; the motion is the same time-based update as everything else. The `ETA` / `MIS` instruments run a forecast of both orbits (about 0.1 ms per frame); the burning of a caught station is a plain formula of time, so it looks the same on any computer.
- **The HUD** is drawn last, in screen pixels, after the globe has been scaled and shifted, which is why it neither grows with the picture nor moves with it.

## Performance

The animation is time-based, so it moves at the same speed whatever the frame rate. If the frame rate is low, it looks less smooth, but it never runs in slow motion.

Measured on the development laptop (macOS, Apple Silicon, Python 3.14, Tk 9.0), frames per second the program can sustain, in the standard 700 x 800 window and in fullscreen:

| | window | fullscreen |
|---|---|---|
| game on, side panel shown (the default) | 83 | 64 |
| game on, panel hidden | 85 | 63 |
| game off, panel shown | 85 | 66 |
| game off, panel hidden | 89 | 65 |

Runs differ by about 3 frames per second. For comparison, the very first version (before any optimisation, no game, no panel, a smaller 700 x 700 window) managed 41 and 31, so the numbers are not strictly like for like, but the picture is now much richer and still about twice as fast.

`TARGET_FPS` is set to 120, which this machine does not reach (see the numbers above); on a faster computer it will. Most of what remains is Tk compositing the two transparent layers (atmosphere and night gradient), not Python.

### Slow computers

With `AUTO_QUALITY = True` (the default; the **Auto-reduce graphics** checkbox) the program watches the real frame rate. It looks at the *median* of the last `QUALITY_WINDOW` (90) frames, so a one-off stall (dragging the window, a system hiccup, the slow first frames) cannot trigger it; only a consistently low rate can. If the median stays below `QUALITY_MIN_FPS` (40), it drops to a simpler level, one step at a time, and never goes back up until the window is resized:

| Level | What is dropped |
|---|---|
| 1 | cloud halo, star twinkling |
| 2 | half of the clouds, satellite trails, the smaller city lights, the atmosphere glow |
| 3 | all clouds, all city lights, all stars |

On a simulated slow machine (every frame artificially made more expensive) this took the frame rate from about 30 to about 60 fps. That is a simulation on a fast laptop, not a measurement on real slow hardware.

If it is still too slow, switch off the heaviest layers in the panel (clouds, atmosphere and day / night cost the most), or lower `CLOUD_SYSTEMS`, `STAR_COUNT`, `SATELLITE_COUNT` and `ATMO_WIDTH`. Untick **Auto-reduce graphics** (or set `AUTO_QUALITY = False`) to always get full detail.

A layer is shown only if its checkbox is ticked **and** the automatic quality level has not dropped it.

## Layout

The program is `index.py` (the frame loop and `main()`) plus the `earth/` package:

```
globe/
├── index.py            - entry point: draw_frame() (what happens every frame) and main()
├── earth/
│   ├── config.py       - all settings: sizes, speeds, colours, game balance
│   ├── state.py        - everything that changes while the program runs
│   ├── data.py         - map data: CONTINENTS and CITIES
│   ├── util.py         - colours, vector maths, PNG encoding
│   ├── night.py        - the day / night curve and the night colours
│   ├── window.py       - the window, the canvas, fast drawing helpers, fullscreen
│   ├── layout.py       - scale and position of the globe and of the HUD
│   ├── geometry.py     - projection of the sphere, polygon helpers
│   ├── land.py         - the continents
│   ├── clouds.py       - the stream of clouds
│   ├── stars.py        - the stars
│   ├── cities.py       - city lights
│   ├── images.py       - pre-rendered atmosphere glow and night gradient
│   ├── scene.py        - the static layer, which layers are visible, automatic quality
│   ├── orbits.py       - orbits of the satellites and of the ISS
│   ├── game.py         - the game: levels, collisions, forecast, burning (logic only)
│   ├── controls.py     - keyboard and mouse
│   ├── sprites.py      - drawing the satellites, the ISS, the turtle, a burning wreck
│   ├── hud.py          - the table of instruments
│   └── panel.py        - the control panel
├── docs/
│   └── screenshot.png
└── README.md
```

Things worth knowing before you change the code:

- **Run `index.py`.** Importing the modules does real work: `earth/window.py` opens the window as soon as it is imported.
- **There are no circular imports.** Each module imports exactly the names it uses (`from earth.config import RADIUS, ...`).
- **A value that is *rebound* while the program runs lives in `earth/state.py` and is used as `state.quality`.** `from earth.state import quality` would give a stale copy that never updates. Things that are only changed in place (the `layer_on` dict, the `recent` list) can be imported by name. Constants never change while the program runs, so they are imported by name.
- `game.py` only computes (it does not even import the window); the drawing of the game's objects is in `sprites.py` and `hud.py`, so the rules of the game can be changed without touching the picture.
