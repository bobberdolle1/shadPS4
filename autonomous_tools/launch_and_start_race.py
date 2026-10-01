import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

root = Path('E:/programming/shadPS4')
log = Path(r'C:\Users\kiril\AppData\Roaming\shadPS4\log\shad_log.txt')
if log.exists():
    log.unlink()

user32 = ctypes.WinDLL('user32', use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
windows = []


def enum_cb(hwnd, _lparam):
    if user32.IsWindowVisible(hwnd):
        n = user32.GetWindowTextLengthW(hwnd)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            windows.append((hwnd, buf.value, pid.value))
    return True


def tap(vk, ms=60):
    user32.keybd_event(vk, 0, 0x0008, 0)
    time.sleep(ms / 1000.0)
    user32.keybd_event(vk, 0, 0x0008 | 0x0002, 0)


VK_RETURN = 0x0D
VK_SPACE = 0x20

argv = [str(root / 'build-clang/shadps4.exe'), str(root),
        '-g', 'E:/Games/emulators/ps4/roms/CUSA49696/eboot.bin', '-f', 'false']
proc = subprocess.Popen(argv, cwd=str(root))

target = None
for phase in range(24):
    time.sleep(5)
    windows.clear()
    user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
    owned = [w for w in windows if w[2] == proc.pid]
    if owned:
        target = owned[0]
        break
print('window:', target[1] if target else None, flush=True)
if target:
    user32.ShowWindow(target[0], 9)
    user32.SetForegroundWindow(target[0])
    time.sleep(1.0)

# Reach the title screen, then confirm the focused Start button with Enter.
print('reached title screen, pressing Enter to start the race', flush=True)
time.sleep(25)
tap(VK_RETURN)
time.sleep(20)
if proc.poll() is None:
    tap(VK_RETURN)
time.sleep(20)

alive = proc.poll() is None
print('emulator alive:', alive, flush=True)
print('exit code:', proc.poll(), flush=True)
sys.exit(0 if alive else 1)
