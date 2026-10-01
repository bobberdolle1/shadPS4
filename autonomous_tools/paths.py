"""Canonical locations for the CUSA49696 research harness.

Every path is overridable through an environment variable so the harness is not tied to one
machine's drive layout. Defaults are derived from this file's own location, which means a
fresh checkout works without editing anything.

Environment variables:

    SHADPS4_REPO      git checkout           (default: the parent of this file)
    SHADPS4_BUILD     out-of-source build     (default: <repo>-build next to the repo)
    SHADPS4_EBOOT     extracted eboot.bin     (default: <repo>/../games/ps4/roms/CUSA49696)
    SHADPS4_USERDATA  emulator user data dir  (default: %APPDATA%/shadPS4)

Note that no game content belongs in this repository: SHADPS4_EBOOT points at a game that is
installed separately and is never committed.
"""
import os
from pathlib import Path

# Repository (git checkout) and its out-of-source build directory.
REPO = Path(os.environ.get('SHADPS4_REPO', Path(__file__).resolve().parent.parent))
BUILD = Path(os.environ.get('SHADPS4_BUILD', REPO.parent / (REPO.name + '-build')))
EXE = BUILD / 'shadps4.exe'

# Game install. Original PKGs live separately and are never modified by the emulator.
GAMES = Path(os.environ.get('SHADPS4_GAMES', REPO.parent / 'games' / 'ps4'))
ROMS = GAMES / 'roms'
DEFAULT_EBOOT = ROMS / 'CUSA49696' / 'eboot.bin'
GAME_EBOOT = Path(os.environ.get('SHADPS4_EBOOT', DEFAULT_EBOOT))

# Emulator user data: settings, logs, screenshots, shader cache.
_default_userdata = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
USERDATA = Path(os.environ.get('SHADPS4_USERDATA', _default_userdata / 'shadPS4'))
LOG = USERDATA / 'log' / 'shad_log.txt'
SCREENSHOTS = USERDATA / 'screenshots'

ARGV = [
    str(EXE), str(REPO),
    '-g', str(GAME_EBOOT),
    '-f', 'false',
]