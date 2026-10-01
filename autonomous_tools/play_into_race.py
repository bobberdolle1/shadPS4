"""Drive My First Gran Turismo from the title screen into a race and screenshot it."""
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

# Paths come from paths.py so this script is not tied to one machine's drive layout.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import EXE, GAME_EBOOT, LOG as log, REPO as root, SCREENSHOTS as shots  # noqa: E402
if log.exists():
    log.unlink()

user32 = ctypes.WinDLL('user32', use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
VK_RETURN, VK_F12, VK_F10 = 0x0D, 0x7B, 0x79

windows = []


def enum_cb(hwnd, _lparam):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    title_len = user32.GetWindowTextLengthW(hwnd)
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls, 256)
    buf = ctypes.create_unicode_buffer(max(title_len, 1) + 1)
    user32.GetWindowTextW(hwnd, buf, title_len + 1)
    windows.append((hwnd, buf.value, cls.value, pid.value, bool(user32.IsWindowVisible(hwnd))))
    return True


def snapshot():
    windows.clear()
    user32.EnumWindows(EnumWindowsProc, 0)
    return list(windows)


def send_key(hwnd, vk):
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
    time.sleep(0.08)
    user32.PostMessageW(hwnd, WM_KEYUP, vk, 0)


argv = [str(EXE), str(root),
        '-g', str(GAME_EBOOT), '-f', 'false']
proc = subprocess.Popen(argv, cwd=str(root))

hwnd = None
for _ in range(60):
    time.sleep(2)
    if proc.poll() is not None:
        print('emulator exited early, code', proc.poll())
        break
    for w in snapshot():
        if w[3] == proc.pid and w[4] and w[1]:
            hwnd = w[0]
            print('window:', hex(hwnd), repr(w[1]), 'class', repr(w[2]))
            break
    if hwnd:
        break

if not hwnd:
    print('no window; visible windows seen:')
    for w in snapshot():
        if w[4]:
            print('  ', hex(w[0]), repr(w[1]), repr(w[2]), 'pid', w[3])
else:
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1)

    # Title screen, then confirm the focused "Start" button.
    print('waiting for title screen')
    time.sleep(80)
    for _ in range(3):
        send_key(hwnd, VK_RETURN)
        time.sleep(3)

    # Give the race load time, then shoot with overlays so the FPS counter shows.
    time.sleep(25)
    send_key(hwnd, VK_F10)
    time.sleep(2)
    send_key(hwnd, VK_F12)
    time.sleep(6)

alive = proc.poll() is None
print('emulator alive:', alive, 'exit:', proc.poll())
new = sorted(set(shots.glob('*.png')) - before)
print('screenshots:', [p.name for p in new])
if not alive:
    tail = log.read_text(errors='replace').splitlines()[-12:] if log.exists() else []
    print('--- log tail ---')
    for line in tail:
        print(line[:160])
sys.exit(0 if alive else 1)