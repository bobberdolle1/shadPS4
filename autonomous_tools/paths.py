"""Canonical locations after the SSD migration.

Everything (dev tree, build, game) lives on F:, the NVMe SSD. Keep path changes here so the
harness scripts never disagree with each other.
"""
from pathlib import Path

# Repository (git checkout) and its out-of-source build directory.
REPO = Path('F:/dev/shadPS4')
BUILD = Path('F:/dev/shadPS4-build')
EXE = BUILD / 'shadps4.exe'

# Game install. Original PKGs live separately and are never modified by the emulator.
GAMES = Path('F:/games/ps4')
ROMS = GAMES / 'roms'
GAME_EBOOT = ROMS / 'CUSA49696' / 'eboot.bin'

# Emulator user data: settings, logs, screenshots, shader cache.
USERDATA = Path(r'C:\Users\kiril\AppData\Roaming\shadPS4')
LOG = USERDATA / 'log' / 'shad_log.txt'
SCREENSHOTS = USERDATA / 'screenshots'

ARGV = [
    str(EXE), str(REPO),
    '-g', str(GAME_EBOOT),
    '-f', 'false',
]
