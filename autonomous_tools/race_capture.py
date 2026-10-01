"""Drive the game on a fixed key schedule and capture the window at fixed timestamps.

The schedule is deterministic so two runs (e.g. GT_DMA_DIRTY=0 vs 1) navigate through
the same states and their screenshots can be compared frame by frame.
"""
import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import paths  # noqa: E402
import wincap  # noqa: E402

from ctypes import wintypes  # noqa: E402

user32 = ctypes.WinDLL('user32', use_last_error=True)
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
VK_RETURN, VK_X, VK_SPACE, VK_DOWN, VK_UP, VK_LEFT, VK_RIGHT = 0x0D, 0x58, 0x20, 0x28, 0x26, 0x25, 0x27

# (seconds_from_start, key) - fixed, identical for every run.
SCHEDULE = []
for t in range(70, 240, 3):
    SCHEDULE.append((t, VK_RETURN))
    if (t - 70) // 3 % 4 == 3:
        SCHEDULE.append((t + 1, VK_X))
SCHEDULE.sort()

# Capture at these timestamps.
SHOTS = [30, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240]

run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('autonomous_logs/race_capture')
duration_s = int(sys.argv[2]) if len(sys.argv) > 2 else 245
run_dir.mkdir(parents=True, exist_ok=True)

if paths.LOG.exists():
    paths.LOG.unlink()

env = dict(os.environ)
proc = subprocess.Popen(paths.ARGV, cwd=str(paths.REPO), env=env)

hwnd = None
deadline = time.time() + 60
while time.time() < deadline and not hwnd:
    time.sleep(2)
    h = wincap.find_window_for_pid(proc.pid)
    if h:
        hwnd = h
print('window:', bool(hwnd))

start = time.time()
next_keys = [i for i, _ in enumerate(SCHEDULE)]
next_shots = list(SHOTS)
taken = []
try:
    while time.time() - start < duration_s:
        el = time.time() - start
        if proc.poll() is not None:
            print('emulator exited early, code', proc.poll())
            break
        while next_keys and SCHEDULE[next_keys[0]][0] <= el:
            _, vk = SCHEDULE[next_keys.pop(0)]
            if hwnd:
                user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
                time.sleep(0.04)
                user32.PostMessageW(hwnd, WM_KEYUP, vk, 0)
        while next_shots and next_shots[0] <= el:
            t = next_shots.pop(0)
            if hwnd:
                try:
                    w, h = wincap.capture(hwnd, run_dir / f'shot_{t:03d}.png')
                    taken.append((t, w, h))
                    print(f'captured t={t}s {w}x{h}')
                except Exception as exc:  # noqa: BLE001
                    print(f'capture failed t={t}: {exc}')
        time.sleep(0.25)
finally:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

print('elapsed', round(time.time() - start, 1), 'shots', taken)
print('=== log tail ===')
if paths.LOG.exists():
    for line in paths.LOG.read_text(errors='replace').splitlines()[-8:]:
        print(line[:160])
