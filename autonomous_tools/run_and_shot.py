import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

# Paths come from paths.py so this script is not tied to one machine's drive layout.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import EXE, GAME_EBOOT, REPO as root, SCREENSHOTS as shots  # noqa: E402
shots.mkdir(parents=True, exist_ok=True)
before = set(shots.glob('*.png'))

user32 = ctypes.WinDLL('user32', use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
found = []

VK_F10 = 0x79
VK_F12 = 0x7B
VK_MENU = 0x12
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002


def tap(vk, alt=False):
    if alt:
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_SCANCODE, 0)
        time.sleep(0.05)
    user32.keybd_event(vk, 0, KEYEVENTF_SCANCODE, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0)
    if alt:
        time.sleep(0.05)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0)


def enum_cb(hwnd, _lparam):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == proc.pid and user32.IsWindowVisible(hwnd):
        found.append(hwnd)
    return True


argv = [str(EXE), str(root),
        '-g', str(GAME_EBOOT), '-f', 'false']
proc = subprocess.Popen(argv, cwd=str(root))
try:
    time.sleep(85)
    user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
    if found:
        user32.ShowWindow(found[0], 9)
        user32.SetForegroundWindow(found[0])
        time.sleep(1.0)
        print('focused', hex(found[0]))
    else:
        print('no visible window')
    tap(VK_F10)          # FPS overlay on
    time.sleep(3)
    tap(VK_F12, alt=True)  # screenshot with overlays
    time.sleep(4)
    tap(VK_F12, alt=True)
    time.sleep(10)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()

new = sorted(set(shots.glob('*.png')) - before)
print('new screenshots:')
for p in new:
    print(' ', p, p.stat().st_size)
sys.exit(0 if new else 1)
