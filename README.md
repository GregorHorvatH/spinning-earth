# Spinning Earth

An animated, rotating globe in pure Python: green continents on a blue ocean, a day/night terminator, city lights, clouds, an atmosphere, satellites and the ISS against a starry sky. No third-party libraries - only the Python standard library.

![Screenshot](docs/screenshot.png)

## Features

- **Day and night** - the left hemisphere is in darkness, with a smooth gradient across the middle.
- **City lights** on the night side (132 major cities, each surrounded by smaller lights). They switch off as a city approaches the daylight.
- **Clouds** - fluffy, with a shadow underneath. They are destroyed past the right horizon and created behind the left one, so there is no visible repeat after a full revolution. They darken at night.
- **Atmosphere** - a translucent glow around the globe that fades out on the night side.
- **10 satellites** on different orbits with trails, and the **ISS** on an orbit with its real 51.6° inclination.
- **Stars** that pulse slowly.
- **Fullscreen** - the picture scales together with the window.
- The animation is driven by real time, so the speed is the same in a window and in fullscreen.

## Requirements

- **Python 3** with **tkinter** support (`turtle` runs on top of it).
- No packages from PyPI are needed: there is no `pip install` step and no `requirements.txt`. The code only imports `math`, `random`, `time` and `turtle`.

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

## Controls

| Action | Result |
|---|---|
| `F` or `F11` | toggle fullscreen |
| double-click the window | same |
| `Esc` | leave fullscreen |
| close the window | quit |

The scale follows the smaller side of the window, so on wide screens the globe simply gets more space around it.

## Configuration

All parameters are constants at the top of [index.py](index.py). Change a value and run it again.

| Constant | What it changes |
|---|---|
| `WIDTH`, `HEIGHT`, `RADIUS` | window and globe size |
| `SPEED` | rotation speed (degrees per frame) |
| `TILT` | tilt of the Earth's axis |
| `OCEAN`, `LAND_FILL`, `LAND_EDGE` | ocean and land colours |
| `NIGHT_START`, `NIGHT_END` | where the day-to-night transition starts and ends |
| `ATMO_COLOR`, `ATMO_WIDTH`, `ATMO_STRENGTH` | colour, thickness and brightness of the atmosphere |
| `CLOUD_SYSTEMS` | number of cloud clusters |
| `STAR_COUNT`, `STAR_TWINKLE` | number of stars and the depth of their pulsing |
| `SATELLITE_COUNT`, `SATELLITE_SEED` | number of satellites and which set of orbits they get |
| `ISS_SPEED`, `ISS_SIZE`, `ISS_INCLINATION`, `ISS_LABEL` | ISS speed, icon size, orbit inclination and the label next to it (empty = no label) |
| `CITY_COLOR`, `CITY_DOTS`, `CITY_VISIBLE_FROM` | colour of the lights, number of smaller lights and how early they switch off |
| `CITIES` | list of cities as `(latitude, longitude)` pairs - add your own |
| `CONTINENTS` | simplified outlines of continents and islands |

## How it works

- The continents are a set of simplified polygons with `(longitude, latitude)` coordinates. They are projected onto a sphere, rotated and drawn on a tkinter canvas.
- The night side is a set of vertical bands of increasing darkness, clipped to the shape of each object. This is how the ocean, land, clouds, satellites and atmosphere all darken consistently.
- The static layer (atmosphere and ocean) is drawn once, and again when the window is resized. The rest of the frame is redrawn every ~25 ms.

## Layout

```
globe/
├── index.py          - the whole program
├── docs/
│   └── screenshot.png
└── README.md
```
