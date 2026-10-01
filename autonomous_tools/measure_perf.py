"""Measure CUSA49696 race-frame cost: DMA sync stats + FPS overlay, driving toward a race."""
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import paths  # noqa: E402

root = paths.REPO
log = paths.LOG
if log.exists():
    log.unlink()

user32 = ctypes.WinDLL('user32', use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
VK_RETURN, VK_X, VK_SPACE = 0x0D, 0x58, 0x20

duration_s = int(sys.argv[1]) if len(sys.argv) > 1 else 210
drive_from = 85
stat = os.environ.get('STATS', '1') == '1'

env = dict(os.environ)
if stat:
    env['CUSA49696_DMA_STATS'] = '1'

argv = paths.ARGV + ['--show-fps']
proc = subprocess.Popen(argv, cwd=str(root), env=env)

windows = []


def enum_cb(hwnd, _lparam):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == proc.pid:
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        windows.append((hwnd, cls.value))
    return True


hwnd = None
deadline = time.time() + 60
while time.time() < deadline:
    time.sleep(2)
    windows.clear()
    user32.EnumWindows(EnumWindowsProc, 0)
    for h, c in windows:
        if c == 'SDL_app':
            hwnd = h
            break
    if hwnd:
        break

if not hwnd:
    print('no SDL window found; windows:', [(hex(h), c) for h, c in windows])

start = time.time()
next_press = drive_from
try:
    while time.time() - start < duration_s:
        time.sleep(0.5)
        if proc.poll() is not None:
            print('emulator exited early, code', proc.poll())
            break
        el = time.time() - start
        if hwnd and el >= next_press:
            for vk in (VK_RETURN, VK_X, VK_SPACE):
                user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
                time.sleep(0.05)
                user32.PostMessageW(hwnd, WM_KEYUP, vk, 0)
            next_press = el + 2.0
finally:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

print('elapsed', round(time.time() - start, 1), 's  window:', bool(hwnd))
if log.exists():
    text = log.read_text(errors='replace')
    lines = text.splitlines()
    stats = [ln for ln in lines if 'DMA_SYNC_STATS' in ln]
    print('=== DMA_SYNC_STATS (last 12) ===')
    for ln in stats[-12:]:
        i = ln.find('DMA_SYNC_STATS')
        print(ln[i:])
    print('=== fps overlay lines ===', sum('FPS' in ln for ln in lines))
    for p in ('Unhandled Exception', 'PM4 stream ends', 'Rejecting invalid T#', 'UpdatePlayTime'):
        print(f'{p:24s} {text.count(p)}')
    print('=== log tail ===')
    for ln in lines[-6:]:
        print(ln[:150])
